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


class RAGSystem:
    def __init__(self, vector_store_type: str = "qdrant"):
        """
        初始化 RAG 系统

        Args:
            vector_store_type: 向量存储类型，支持 "faiss" 或 "qdrant"
        """
        self.document_loader = DocumentLoader()
        self.text_splitter = TextSplitter()
        self.llm_integration = LLMIntegration()
        self.vector_store: Optional[Union[FAISS, Qdrant]] = None
        self.embeddings: Optional[Embeddings] = None
        self.vector_store_type = vector_store_type.lower()
        self.prompt_builder = RAGPromptBuilder()

        # Qdrant 配置
        self.qdrant_collection_name = "langchain_documents"
        self.qdrant_persist_dir = "./qdrant_storage"

        logger.info(f"Initialized RAG system with vector store type: {vector_store_type}")

    def setup_embeddings(self):
        """设置嵌入模型"""
        self.embeddings = OpenAIEmbeddings()
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
        # 确保 embeddings 已初始化
        assert self.embeddings is not None, "Embeddings must be initialized"

        # 创建持久化目录
        os.makedirs(self.qdrant_persist_dir, exist_ok=True)

        # 创建 Qdrant 客户端（本地模式）

        # 创建向量存储
        vector_store = Qdrant.from_documents(
            documents=documents,
            embedding=self.embeddings,
            url=None,  # 使用本地模式
            path=self.qdrant_persist_dir,
            collection_name=self.qdrant_collection_name,
            force_recreate=True,
        )

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

    def retrieve_documents(self, query: str, k: int = 3):
        """检索相关文档"""
        if not self.vector_store:
            raise ValueError("向量存储未初始化，请先调用 create_vector_store")

        # 相似度搜索
        results = self.vector_store.similarity_search(query=query, k=k)

        return results

    def retrieve_documents_with_scores(self, query: str, k: int = 3):
        """检索相关文档并返回相似度分数"""
        if not self.vector_store:
            raise ValueError("向量存储未初始化，请先调用 create_vector_store")

        # 相似度搜索（带分数）
        results = self.vector_store.similarity_search_with_score(query=query, k=k)

        return results

    def generate_answer(
        self,
        query: str,
        k: int = 3,
        template_type: PromptTemplateType = PromptTemplateType.RAG_QA,
        max_context_length: int = 4000,
    ):
        """
        生成基于检索文档的回答

        Args:
            query: 用户问题
            k: 检索文档数量
            template_type: 提示模板类型
            max_context_length: 最大上下文长度

        Returns:
            (回答, 相关文档列表)
        """
        logger.info(f"Generating answer for query: {query[:50]}...")

        # 检索相关文档
        relevant_docs = self.retrieve_documents(query, k)

        if not relevant_docs:
            logger.warning("No relevant documents found")
            return "抱歉，没有找到相关的文档信息。", []

        # 使用提示构建器构建提示
        prompt = self.prompt_builder.build_qa_prompt(
            query=query, documents=relevant_docs, max_context_length=max_context_length
        )

        # 生成回答
        answer = self.llm_integration.generate(prompt)

        logger.info("Generated answer successfully")
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

    def load_and_process_documents(self, file_paths: List[str]):
        """加载和处理文档"""
        all_docs = []

        for file_path in file_paths:
            docs = self.document_loader.load_document(file_path)
            all_docs.extend(docs)

        return all_docs

    def save_vector_store(self, file_path: str):
        """保存向量存储"""
        if not self.vector_store:
            raise ValueError("向量存储未初始化，请先调用 create_vector_store")

        if self.vector_store_type == "faiss":
            if isinstance(self.vector_store, FAISS):
                self.vector_store.save_local(file_path)
        else:
            # Qdrant 自动持久化，无需手动保存
            print(f"Qdrant 向量存储已自动保存到 {self.qdrant_persist_dir}")

        return True

    def load_vector_store(self, file_path: str):
        """加载向量存储"""
        if not self.embeddings:
            self.setup_embeddings()

        # 确保 embeddings 已初始化
        assert self.embeddings is not None, "Embeddings must be initialized"

        if self.vector_store_type == "faiss":
            self.vector_store = FAISS.load_local(
                folder_path=file_path,
                embeddings=self.embeddings,
                allow_dangerous_deserialization=True,
            )
        else:
            # 加载 Qdrant 向量存储
            if not os.path.exists(self.qdrant_persist_dir):
                raise ValueError(f"Qdrant 存储目录不存在: {self.qdrant_persist_dir}")

            client = QdrantClient(path=self.qdrant_persist_dir)

            self.vector_store = Qdrant(
                client=client,
                collection_name=self.qdrant_collection_name,
                embeddings=self.embeddings,
            )

        return self.vector_store

    def delete_collection(self):
        """删除向量存储集合（仅 Qdrant）"""
        if self.vector_store_type == "qdrant":
            client = QdrantClient(path=self.qdrant_persist_dir)
            try:
                client.delete_collection(self.qdrant_collection_name)
                print(f"已删除集合: {self.qdrant_collection_name}")
            except Exception as e:
                print(f"删除集合失败: {e}")

    def get_collection_info(self):
        """获取向量存储信息"""
        if self.vector_store_type == "qdrant":
            client = QdrantClient(path=self.qdrant_persist_dir)
            try:
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
