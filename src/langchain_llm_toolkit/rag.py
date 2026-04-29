from typing import List, Optional, Union
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS, Qdrant
from langchain_openai import OpenAIEmbeddings
from langchain_core.embeddings import Embeddings
from qdrant_client import QdrantClient
from langchain_llm_toolkit.document_loader import DocumentLoader
from langchain_llm_toolkit.text_splitter import TextSplitter
from langchain_llm_toolkit.llm_integration import LLMIntegration
from langchain_llm_toolkit.prompt_templates import RAGPromptBuilder, PromptTemplateType
from langchain_llm_toolkit.logger import logger
import os
import hashlib
from functools import lru_cache
from datetime import datetime, timedelta


class QueryCache:
    """查询缓存 - 提升检索性能"""

    def __init__(self, max_size: int = 100, ttl_seconds: int = 3600):
        self._cache: dict = {}
        self._max_size = max_size
        self._ttl = timedelta(seconds=ttl_seconds)

    def _hash_query(self, query: str, k: int) -> str:
        return hashlib.md5(f"{query}:{k}".encode()).hexdigest()

    def get(self, query: str, k: int) -> Optional[List[Document]]:
        key = self._hash_query(query, k)
        if key in self._cache:
            entry = self._cache[key]
            if datetime.now() - entry["time"] < self._ttl:
                logger.debug(f"Cache hit for query: {query[:50]}...")
                return entry["docs"]
            else:
                del self._cache[key]
        return None

    def set(self, query: str, k: int, docs: List[Document]):
        if len(self._cache) >= self._max_size:
            oldest = min(self._cache.items(), key=lambda x: x[1]["time"])
            del self._cache[oldest[0]]

        key = self._hash_query(query, k)
        self._cache[key] = {"docs": docs, "time": datetime.now()}
        logger.debug(f"Cached query: {query[:50]}...")

    def clear(self):
        self._cache.clear()
        logger.info("Query cache cleared")


class OllamaEmbeddingsWrapper(Embeddings):
    """Ollama Embeddings 包装器 - 解决版本兼容问题"""

    MODELS_NEED_NUM_CTX = {"nomic-embed-text"}

    def __init__(
        self,
        model: str = "nomic-embed-text",
        base_url: str = "http://localhost:11434",
        num_ctx: int = 8192,
    ):
        self.model = model
        self.base_url = base_url
        self.num_ctx = num_ctx
        self._use_options = model in self.MODELS_NEED_NUM_CTX
        try:
            import ollama

            self._client = ollama.Client(host=base_url)
        except ImportError:
            raise ImportError("请安装 ollama: pip install ollama")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """嵌入多个文档"""
        embeddings = []
        for text in texts:
            if self._use_options:
                response = self._client.embeddings(
                    model=self.model, prompt=text, options={"num_ctx": self.num_ctx}
                )
            else:
                response = self._client.embeddings(model=self.model, prompt=text)
            embeddings.append(response["embedding"])
        return embeddings

    def embed_query(self, text: str) -> List[float]:
        """嵌入查询"""
        if self._use_options:
            response = self._client.embeddings(
                model=self.model, prompt=text, options={"num_ctx": self.num_ctx}
            )
        else:
            response = self._client.embeddings(model=self.model, prompt=text)
        return response["embedding"]


class RAGSystem:
    def __init__(
        self,
        vector_store_type: str = "qdrant",
        embedding_type: str = "ollama",
        embedding_model: str = "snowflake-arctic-embed2",
        llm_model: str = "ollama/gemma4",
        qdrant_persist_dir: Optional[str] = None,
        faiss_persist_dir: Optional[str] = None,
        collection_name: Optional[str] = None,
        timeout: int = 120,
        qdrant_url: Optional[str] = None,
        qdrant_api_key: Optional[str] = None,
    ):
        """
        初始化 RAG 系统

        Args:
            vector_store_type: 向量存储类型，支持 "faiss" 或 "qdrant"
            embedding_type: 嵌入模型类型，支持 "openai" 或 "ollama"
            embedding_model: 嵌入模型名称（仅 Ollama）
            llm_model: LLM 模型名称，支持 "ollama/*" 或 OpenAI 模型
            qdrant_persist_dir: Qdrant 存储目录（默认从环境变量读取）
            faiss_persist_dir: FAISS 存储目录（默认从环境变量读取）
            collection_name: 集合名称（默认从环境变量读取）
            timeout: LLM 请求超时时间（秒）
            qdrant_url: Qdrant Server URL（可选，使用服务器模式）
            qdrant_api_key: Qdrant Server API Key（可选）
        """
        self.document_loader = DocumentLoader()
        self.text_splitter = TextSplitter()
        self.llm_integration = LLMIntegration(timeout=timeout)
        self.llm_integration.set_model(llm_model)
        self.vector_store: Optional[Union[FAISS, Qdrant]] = None
        self.embeddings: Optional[Embeddings] = None
        self.vector_store_type = vector_store_type.lower()
        self.embedding_type = embedding_type.lower()
        self.embedding_model = embedding_model
        self.llm_model = llm_model
        self.prompt_builder = RAGPromptBuilder()
        self.query_cache = QueryCache(max_size=100, ttl_seconds=3600)
        self.qdrant_url = qdrant_url or os.environ.get("QDRANT_URL")
        self.qdrant_api_key = qdrant_api_key or os.environ.get("QDRANT_API_KEY")

        self.qdrant_collection_name = collection_name or os.environ.get(
            "RAG_COLLECTION_NAME", "langchain_documents"
        )
        self.qdrant_persist_dir = qdrant_persist_dir or os.environ.get(
            "RAG_QDRANT_PATH", "./qdrant_storage"
        )
        self.faiss_persist_dir = faiss_persist_dir or os.environ.get(
            "RAG_FAISS_PATH", "./vector_store"
        )

        logger.info(
            f"Initialized RAG system with vector store type: {vector_store_type}, "
            f"embedding type: {embedding_type}, llm model: {llm_model}"
        )
        if self.qdrant_url:
            logger.info(f"Using Qdrant Server: {self.qdrant_url}")
        else:
            logger.info(f"Using local Qdrant storage: {self.qdrant_persist_dir}")

    def setup_embeddings(self):
        """设置嵌入模型"""
        if self.embedding_type == "ollama":
            ollama_base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
            self.embeddings = OllamaEmbeddingsWrapper(
                model=self.embedding_model, base_url=ollama_base_url, num_ctx=8192
            )
            logger.info(f"Using Ollama embeddings with model: {self.embedding_model}")
        else:
            self.embeddings = OpenAIEmbeddings()
            logger.info("Using OpenAI embeddings")
        return self.embeddings

    def create_vector_store(self, documents: List[Document]):
        """创建向量存储"""
        if not self.embeddings:
            self.setup_embeddings()

        # 确保 embeddings 已初始化
        assert self.embeddings is not None, "Embeddings must be initialized"

        # 分割文档
        split_docs = self.text_splitter.split_documents(documents)

        # 根据类型创建向量存储
        if self.vector_store_type == "qdrant":
            self.vector_store = self._create_qdrant_store(split_docs)
        else:
            self.vector_store = self._create_faiss_store(split_docs)

        return self.vector_store

    def _create_qdrant_store(self, documents: List[Document]):
        """创建 Qdrant 向量存储"""
        assert self.embeddings is not None, "Embeddings must be initialized"

        if self.qdrant_url:
            client = QdrantClient(
                url=self.qdrant_url,
                api_key=self.qdrant_api_key,
            )
        else:
            os.makedirs(self.qdrant_persist_dir, exist_ok=True)
            client = QdrantClient(path=self.qdrant_persist_dir)

        from qdrant_client.http import models as rest

        sample_embedding = self.embeddings.embed_query("test")
        vector_size = len(sample_embedding)

        client.recreate_collection(
            collection_name=self.qdrant_collection_name,
            vectors_config=rest.VectorParams(
                size=vector_size,
                distance=rest.Distance.COSINE,
            ),
        )

        vector_store = Qdrant(
            client=client,
            collection_name=self.qdrant_collection_name,
            embeddings=self.embeddings,
        )

        # 添加文档
        vector_store.add_documents(documents)

        return vector_store

    def _create_faiss_store(self, documents: List[Document]):
        """创建 FAISS 向量存储"""
        # 确保 embeddings 已初始化
        assert self.embeddings is not None, "Embeddings must be initialized"

        vector_store = FAISS.from_documents(documents=documents, embedding=self.embeddings)
        return vector_store

    def add_documents(self, documents: List[Document]):
        """向向量存储添加文档"""
        if not self.vector_store:
            raise ValueError("向量存储未初始化，请先调用 create_vector_store")

        # 分割文档
        split_docs = self.text_splitter.split_documents(documents)

        # 添加到向量存储
        self.vector_store.add_documents(split_docs)

        return self.vector_store

    def retrieve_documents(self, query: str, k: int = 3, score_threshold: float = 0.0, use_cache: bool = True):
        """检索相关文档

        Args:
            query: 查询文本
            k: 返回文档数量
            score_threshold: 相似度阈值（0-1），低于此阈值的文档将被过滤
            use_cache: 是否使用缓存，默认 True

        Returns:
            相关文档列表
        """
        if not self.vector_store:
            raise ValueError("向量存储未初始化，请先调用 create_vector_store")

        if use_cache and score_threshold == 0:
            cached = self.query_cache.get(query, k)
            if cached is not None:
                return cached

        if score_threshold > 0:
            results = self.vector_store.similarity_search_with_score(query=query, k=k * 2)
            filtered = [(doc, score) for doc, score in results if score >= score_threshold]
            docs = [doc for doc, _ in filtered[:k]]
        else:
            docs = self.vector_store.similarity_search(query=query, k=k)

        if use_cache and score_threshold == 0:
            self.query_cache.set(query, k, docs)

        return docs

    def retrieve_documents_with_scores(self, query: str, k: int = 3, score_threshold: float = 0.0):
        """检索相关文档并返回相似度分数

        Args:
            query: 查询文本
            k: 返回文档数量
            score_threshold: 相似度阈值

        Returns:
            (文档, 分数) 列表
        """
        if not self.vector_store:
            raise ValueError("向量存储未初始化，请先调用 create_vector_store")

        results = self.vector_store.similarity_search_with_score(query=query, k=k * 2)

        if score_threshold > 0:
            results = [(doc, score) for doc, score in results if score >= score_threshold]

        return results[:k]

    def rerank_documents(
        self, query: str, documents: List[Document], top_k: int = 3
    ) -> List[Document]:
        """重排序文档 - 使用 LLM 对检索结果进行重排序

        Args:
            query: 查询文本
            documents: 待重排序的文档列表
            top_k: 返回的文档数量

        Returns:
            重排序后的文档列表
        """
        if len(documents) <= top_k:
            return documents

        rerank_prompt = f"""请根据与问题的相关性，对以下文档片段进行排序。

问题: {query}

文档片段:
"""
        for i, doc in enumerate(documents[:10], 1):
            content = doc.page_content[:200]
            rerank_prompt += f"\n[文档{i}]: {content}..."

        rerank_prompt += """

请返回最相关的文档编号，按相关性从高到低排列，格式如: 3,1,5,2,4
只返回编号，不要其他内容。"""

        try:
            response = self.llm_integration.generate(rerank_prompt)
            indices = [int(x.strip()) - 1 for x in response.split(",") if x.strip().isdigit()]
            indices = [i for i in indices if 0 <= i < len(documents)]
            while len(indices) < top_k and len(indices) < len(documents):
                for i in range(len(documents)):
                    if i not in indices:
                        indices.append(i)
                        break
            return [documents[i] for i in indices[:top_k]]
        except Exception:
            return documents[:top_k]

    def generate_answer(
        self,
        query: str,
        k: int = 3,
        template_type: PromptTemplateType = PromptTemplateType.RAG_QA,
        max_context_length: int = 4000,
        score_threshold: float = 0.0,
        use_rerank: bool = False,
        use_cache: bool = True,
    ):
        """
        生成基于检索文档的回答

        Args:
            query: 用户问题
            k: 检索文档数量
            template_type: 提示模板类型
            max_context_length: 最大上下文长度
            score_threshold: 相似度阈值
            use_rerank: 是否使用重排序
            use_cache: 是否使用缓存

        Returns:
            (回答, 相关文档列表)
        """
        import time
        from langchain_llm_toolkit.performance import query_cache, performance_monitor

        start_time = time.time()

        if use_cache:
            cached = query_cache.get(query, k, use_rerank=use_rerank)
            if cached:
                logger.info(f"Cache hit for query: {query[:30]}...")
                return cached["answer"], cached["documents"]

        logger.info(f"Generating answer for query: {query[:50]}...")

        relevant_docs = self.retrieve_documents(query, k * 2 if use_rerank else k, score_threshold)

        if not relevant_docs:
            logger.warning("No relevant documents found")
            return "抱歉，没有找到相关的文档信息。", []

        if use_rerank:
            relevant_docs = self.rerank_documents(query, relevant_docs, k)

        prompt = self.prompt_builder.build_qa_prompt(
            query=query, documents=relevant_docs, max_context_length=max_context_length
        )

        answer = self.llm_integration.generate(prompt)

        elapsed_time = time.time() - start_time
        performance_monitor.record("rag_generate_time", elapsed_time)

        if use_cache:
            query_cache.set(
                query, {"answer": answer, "documents": relevant_docs}, k, use_rerank=use_rerank
            )

        logger.info(f"Generated answer successfully in {elapsed_time:.2f}s")
        return answer, relevant_docs

    def generate_summary(self, documents: List[Document], max_context_length: int = 4000):
        """
        生成文档摘要

        Args:
            documents: 文档列表
            max_context_length: 最大上下文长度

        Returns:
            摘要
        """
        logger.info(f"Generating summary for {len(documents)} documents")

        prompt = self.prompt_builder.build_summary_prompt(
            documents=documents, max_context_length=max_context_length
        )

        summary = self.llm_integration.generate(prompt)
        logger.info("Summary generated successfully")
        return summary

    def extract_information(
        self, documents: List[Document], extract_type: str, max_context_length: int = 4000
    ):
        """
        从文档中提取信息

        Args:
            documents: 文档列表
            extract_type: 提取类型（如"关键信息"、"日期"、"人名"等）
            max_context_length: 最大上下文长度

        Returns:
            提取的信息
        """
        logger.info(f"Extracting {extract_type} from {len(documents)} documents")

        prompt = self.prompt_builder.build_extraction_prompt(
            documents=documents, extract_type=extract_type, max_context_length=max_context_length
        )

        result = self.llm_integration.generate(prompt)
        logger.info("Information extracted successfully")
        return result

    def load_and_process_documents(self, file_paths: List[str], parallel: bool = True):
        """加载和处理文档

        Args:
            file_paths: 文件路径列表
            parallel: 是否并行处理

        Returns:
            文档列表
        """
        if parallel and len(file_paths) > 1:
            from langchain_llm_toolkit.performance import get_parallel_processor

            def process_file(file_path: str):
                try:
                    return self.document_loader.load_document(file_path)
                except Exception as e:
                    logger.warning(f"Failed to load {file_path}: {e}")
                    return []

            processor = get_parallel_processor()
            results = processor.process_batch(process_file, file_paths)
            all_docs = []
            for docs in results:
                all_docs.extend(docs)
            return all_docs
        else:
            all_docs = []
            for file_path in file_paths:
                docs = self.document_loader.load_document(file_path)
                all_docs.extend(docs)
            return all_docs

    def save_vector_store(self, file_path: Optional[str] = None):
        """保存向量存储

        Args:
            file_path: 保存路径（可选，默认使用配置的路径）
        """
        if not self.vector_store:
            raise ValueError("向量存储未初始化，请先调用 create_vector_store")

        if self.vector_store_type == "faiss":
            save_path = file_path or self.faiss_persist_dir
            if isinstance(self.vector_store, FAISS):
                self.vector_store.save_local(save_path)
                logger.info(f"FAISS 向量存储已保存到 {save_path}")
        else:
            # Qdrant 自动持久化，无需手动保存
            logger.info(f"Qdrant 向量存储已自动保存到 {self.qdrant_persist_dir}")

        return True

    def load_vector_store(self, file_path: Optional[str] = None):
        """加载向量存储

        Args:
            file_path: 加载路径（可选，默认使用配置的路径）
        """
        if not self.embeddings:
            self.setup_embeddings()

        assert self.embeddings is not None, "Embeddings must be initialized"

        if self.vector_store_type == "faiss":
            load_path = file_path or self.faiss_persist_dir
            self.vector_store = FAISS.load_local(
                folder_path=load_path,
                embeddings=self.embeddings,
                allow_dangerous_deserialization=True,
            )
            logger.info(f"FAISS 向量存储已从 {load_path} 加载")
        else:
            if self.qdrant_url:
                client = QdrantClient(
                    url=self.qdrant_url,
                    api_key=self.qdrant_api_key,
                )
                logger.info(f"Qdrant 向量存储已从服务器加载: {self.qdrant_url}")
            else:
                if not os.path.exists(self.qdrant_persist_dir):
                    raise ValueError(f"Qdrant 存储目录不存在: {self.qdrant_persist_dir}")

                client = QdrantClient(path=self.qdrant_persist_dir)
                logger.info(f"Qdrant 向量存储已从 {self.qdrant_persist_dir} 加载")

            self.vector_store = Qdrant(
                client=client,
                collection_name=self.qdrant_collection_name,
                embeddings=self.embeddings,
            )

        return self.vector_store

    def delete_collection(self):
        """删除向量存储集合（仅 Qdrant）"""
        if self.vector_store_type == "qdrant":
            if self.vector_store is None:
                print("向量存储未初始化")
                return
            try:
                client = self.vector_store.client
                client.delete_collection(self.qdrant_collection_name)
                print(f"已删除集合: {self.qdrant_collection_name}")
            except Exception as e:
                print(f"删除集合失败: {e}")

    def delete_documents_by_source(self, source: str) -> int:
        """按来源删除文档（仅 Qdrant）

        Args:
            source: 文档来源路径

        Returns:
            删除的文档数量
        """
        if self.vector_store_type != "qdrant":
            logger.warning("FAISS 不支持按条件删除")
            return 0

        if self.vector_store is None:
            logger.warning("向量存储未初始化")
            return 0

        try:
            from qdrant_client.http import models as rest

            client = self.vector_store.client

            client.delete(
                collection_name=self.qdrant_collection_name,
                points_selector=rest.FilterSelector(
                    filter=rest.Filter(
                        must=[
                            rest.FieldCondition(
                                key="metadata.source",
                                match=rest.MatchValue(value=source),
                            )
                        ]
                    )
                ),
            )
            logger.info(f"已删除来源为 {source} 的文档")
            return 1
        except Exception as e:
            logger.error(f"删除文档失败: {e}")
            return 0

    def update_document(self, file_path: str) -> bool:
        """更新单个文档（删除旧的，添加新的）

        Args:
            file_path: 文档文件路径

        Returns:
            是否成功
        """
        if not self.vector_store:
            self.load_vector_store()

        try:
            self.delete_documents_by_source(file_path)
            documents = self.load_and_process_documents([file_path])
            if documents:
                self.add_documents(documents)
                logger.info(f"已更新文档: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"更新文档失败: {e}")
            return False

    def get_collection_info(self):
        """获取向量存储信息"""
        if self.vector_store_type == "qdrant":
            if self.vector_store is None:
                return {"error": "向量存储未初始化"}
            try:
                client = self.vector_store.client
                info = client.get_collection(self.qdrant_collection_name)
                return {
                    "points_count": info.points_count,
                    "vectors_count": info.vectors_count,
                    "status": info.status.value,
                }
            except Exception as e:
                return {"error": str(e)}
        else:
            return {"type": "FAISS", "info": "FAISS 不支持集合信息查询"}

    def search_by_metadata(
        self,
        query: str,
        filter_metadata: Optional[dict] = None,
        k: int = 3,
    ) -> List[Document]:
        """按元数据过滤检索文档

        Args:
            query: 查询文本
            filter_metadata: 元数据过滤条件，如 {"category": "技术实现", "tags": "IRR"}
            k: 返回文档数量

        Returns:
            过滤后的文档列表
        """
        if not self.vector_store:
            raise ValueError("向量存储未初始化，请先调用 create_vector_store")

        if self.vector_store_type == "qdrant":
            from qdrant_client.http import models as rest

            must_conditions = []
            for key, value in filter_metadata.items() if filter_metadata else []:
                must_conditions.append(
                    rest.FieldCondition(
                        key=f"metadata.{key}",
                        match=rest.MatchValue(value=value),
                    )
                )

            search_filter = rest.Filter(must=must_conditions) if must_conditions else None

            results = self.vector_store.similarity_search_with_score(
                query=query,
                k=k,
                filter=search_filter,
            )
            return [doc for doc, _ in results]
        else:
            results = self.vector_store.similarity_search(query=query, k=k * 3)
            filtered = []
            for doc in results:
                match = True
                if filter_metadata:
                    for key, value in filter_metadata.items():
                        if doc.metadata.get(key) != value:
                            match = False
                            break
                if match:
                    filtered.append(doc)
                if len(filtered) >= k:
                    break
            return filtered

    def search_by_name(
        self,
        name: str,
        k: int = 5,
    ) -> List[Document]:
        """按文档名称搜索

        Args:
            name: 文档名称（模糊匹配）
            k: 返回文档数量

        Returns:
            匹配的文档列表
        """
        if not self.vector_store:
            raise ValueError("向量存储未初始化")

        results = self.vector_store.similarity_search(query=name, k=k * 3)

        filtered = []
        name_lower = name.lower()
        for doc in results:
            doc_name = doc.metadata.get("name", "").lower()
            source = doc.metadata.get("source", "").lower()

            if name_lower in doc_name or name_lower in source:
                filtered.append(doc)
            if len(filtered) >= k:
                break

        return filtered

    def search_by_tags(
        self,
        tags: List[str],
        k: int = 5,
        match_all: bool = False,
    ) -> List[Document]:
        """按标签搜索文档

        Args:
            tags: 标签列表
            k: 返回文档数量
            match_all: 是否需要匹配所有标签

        Returns:
            匹配的文档列表
        """
        if not self.vector_store:
            raise ValueError("向量存储未初始化")

        query = " ".join(tags)
        results = self.vector_store.similarity_search(query=query, k=k * 5)

        filtered = []
        for doc in results:
            doc_tags = doc.metadata.get("tags", [])
            if isinstance(doc_tags, str):
                doc_tags = [doc_tags]

            if match_all:
                if all(tag in doc_tags for tag in tags):
                    filtered.append(doc)
            else:
                if any(tag in doc_tags for tag in tags):
                    filtered.append(doc)

            if len(filtered) >= k:
                break

        return filtered

    def search_by_category(
        self,
        category: str,
        query: Optional[str] = None,
        k: int = 5,
    ) -> List[Document]:
        """按分类搜索文档

        Args:
            category: 分类名称
            query: 可选的查询文本
            k: 返回文档数量

        Returns:
            匹配的文档列表
        """
        return self.search_by_metadata(
            query=query or category,
            filter_metadata={"category": category},
            k=k,
        )

    def hybrid_search(
        self,
        query: str,
        filter_metadata: Optional[dict] = None,
        k: int = 5,
        alpha: float = 0.7,
    ) -> List[tuple]:
        """混合检索：向量检索 + 元数据过滤

        Args:
            query: 查询文本
            filter_metadata: 元数据过滤条件
            k: 返回文档数量
            alpha: 向量检索权重（0-1），1-alpha 为元数据匹配权重

        Returns:
            (文档, 综合得分) 列表
        """
        if not self.vector_store:
            raise ValueError("向量存储未初始化")

        results = self.vector_store.similarity_search_with_score(query=query, k=k * 3)

        scored_results = []
        for doc, vector_score in results:
            metadata_score = 1.0
            if filter_metadata:
                match_count = 0
                total_conditions = len(filter_metadata)
                for key, value in filter_metadata.items():
                    doc_value = doc.metadata.get(key)
                    if doc_value == value:
                        match_count += 1
                    elif isinstance(doc_value, list) and value in doc_value:
                        match_count += 1
                metadata_score = match_count / total_conditions if total_conditions > 0 else 1.0

            combined_score = alpha * vector_score + (1 - alpha) * metadata_score
            scored_results.append((doc, combined_score, vector_score, metadata_score))

        scored_results.sort(key=lambda x: x[1], reverse=True)

        return [(doc, score) for doc, score, _, _ in scored_results[:k]]

    def list_documents(
        self,
        limit: int = 100,
        offset: int = 0,
        category: Optional[str] = None,
    ) -> List[dict]:
        """列出知识库中的文档

        Args:
            limit: 返回数量限制
            offset: 偏移量
            category: 按分类过滤

        Returns:
            文档元数据列表
        """
        if not self.vector_store:
            raise ValueError("向量存储未初始化")

        if self.vector_store_type == "qdrant":
            from qdrant_client.http import models as rest

            client = self.vector_store.client

            scroll_filter = None
            if category:
                scroll_filter = rest.Filter(
                    must=[
                        rest.FieldCondition(
                            key="metadata.category",
                            match=rest.MatchValue(value=category),
                        )
                    ]
                )

            results, _ = client.scroll(
                collection_name=self.qdrant_collection_name,
                limit=limit,
                offset=offset,
                with_payload=True,
                with_vectors=False,
                scroll_filter=scroll_filter,
            )

            documents = []
            seen_sources = set()
            for point in results:
                payload = point.payload or {}
                metadata = payload.get("metadata", {})
                source = metadata.get("source", "")

                if source and source not in seen_sources:
                    seen_sources.add(source)
                    documents.append({
                        "id": str(point.id),
                        "name": metadata.get("name", source),
                        "description": metadata.get("description", ""),
                        "tags": metadata.get("tags", []),
                        "category": metadata.get("category", ""),
                        "source": source,
                    })

            return documents
        else:
            return [{"type": "FAISS", "info": "FAISS 不支持文档列表查询"}]

    def get_document_count(self) -> int:
        """获取文档数量"""
        info = self.get_collection_info()
        return info.get("points_count", 0)


def test_rag_system():
    """测试 RAG 系统"""
    print("测试 RAG 系统（Qdrant 版本）...")

    # 初始化 RAG 系统
    rag_system = RAGSystem(vector_store_type="qdrant")

    # 加载示例文档
    print("\n1. 加载示例文档...")
    test_file = "test_document.txt"

    # 创建测试文档
    with open(test_file, "w", encoding="utf-8") as f:
        f.write("LangChain 是一个用于开发基于语言模型的应用程序的框架。\n\n")
        f.write("它提供了一系列工具和组件，使得开发者可以更轻松地构建复杂的 LLM 应用。\n\n")
        f.write("LangChain 的主要组件包括：\n")
        f.write("1. 文档加载器：用于加载各种格式的文档\n")
        f.write("2. 文本分割器：用于将长文本分割为更小的片段\n")
        f.write("3. 向量存储：用于存储和检索文本嵌入\n")
        f.write("4. 语言模型集成：用于与各种 LLM 进行交互\n")
        f.write("5. 链：用于组合多个组件以实现复杂功能\n\n")
        f.write(
            "RAG (Retrieval Augmented Generation) 是 LangChain 中的一个重要应用场景，"
            "它结合了检索和生成功能，使得语言模型可以基于外部知识生成更准确的回答。"
        )

    # 加载和处理文档
    documents = rag_system.load_and_process_documents([test_file])
    print(f"加载了 {len(documents)} 个文档")

    # 创建向量存储
    print("\n2. 创建向量存储（Qdrant）...")
    rag_system.create_vector_store(documents)
    print("向量存储创建成功")

    # 获取集合信息
    print("\n3. 获取向量存储信息...")
    info = rag_system.get_collection_info()
    print(f"集合信息: {info}")

    # 测试检索
    print("\n4. 测试检索功能...")
    query = "LangChain 的主要组件有哪些？"
    relevant_docs = rag_system.retrieve_documents(query)
    print(f"检索到 {len(relevant_docs)} 个相关文档")
    for i, doc in enumerate(relevant_docs):
        print(f"\n相关文档 {i+1}:")
        print(doc.page_content[:100] + "..." if len(doc.page_content) > 100 else doc.page_content)

    # 测试带分数的检索
    print("\n5. 测试带分数的检索...")
    results_with_scores = rag_system.retrieve_documents_with_scores(query)
    for i, (doc, score) in enumerate(results_with_scores):
        print(f"文档 {i+1} - 相似度分数: {score:.4f}")
        print(doc.page_content[:80] + "...")

    # 测试生成回答
    print("\n6. 测试生成回答功能...")
    answer, _ = rag_system.generate_answer(query)
    print(f"问题: {query}")
    print(f"回答: {answer}")

    # 测试另一个问题
    query2 = "什么是 RAG？"
    answer2, _ = rag_system.generate_answer(query2)
    print(f"\n问题: {query2}")
    print(f"回答: {answer2}")

    # 保存向量存储
    print("\n7. 保存向量存储...")
    rag_system.save_vector_store("vector_store")
    print("向量存储保存成功")

    # 加载向量存储
    print("\n8. 加载向量存储...")
    rag_system2 = RAGSystem(vector_store_type="qdrant")
    rag_system2.load_vector_store("vector_store")
    print("向量存储加载成功")

    # 测试加载后的向量存储
    print("\n9. 测试加载后的向量存储...")
    answer3, _ = rag_system2.generate_answer(query)
    print(f"问题: {query}")
    print(f"回答: {answer3}")

    print("\n测试完成！")


if __name__ == "__main__":
    test_rag_system()
