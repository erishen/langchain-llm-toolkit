import math
import re
from collections import Counter

from langchain_core.documents import Document


class BM25:
    """BM25 关键词检索算法

    Okapi BM25 算法实现，用于关键词检索。
    """

    def __init__(
        self,
        k1: float = 1.5,
        b: float = 0.75,
        epsilon: float = 0.25,
    ):
        """
        初始化 BM25

        Args:
            k1: 词频饱和参数
            b: 文档长度归一化参数
            epsilon: IDF 下限
        """
        self.k1 = k1
        self.b = b
        self.epsilon = epsilon
        self.doc_freqs: dict[str, int] = {}
        self.doc_len: list[int] = []
        self.avgdl: float = 0
        self.doc_count: int = 0
        self.doc_term_freqs: list[dict[str, int]] = []
        self.idf: dict[str, float] = {}
        self.documents: list[Document] = []

    def _tokenize(self, text: str) -> list[str]:
        """分词"""
        text = text.lower()
        tokens = re.findall(r"\w+", text)
        return tokens

    def fit(self, documents: list[Document]):
        """训练 BM25 模型"""
        self.documents = documents
        self.doc_count = len(documents)
        self.doc_len = []
        self.doc_term_freqs = []
        self.doc_freqs = {}

        for doc in documents:
            tokens = self._tokenize(doc.page_content)
            self.doc_len.append(len(tokens))
            term_freqs = Counter(tokens)
            self.doc_term_freqs.append(dict(term_freqs))

            for term in term_freqs:
                if term not in self.doc_freqs:
                    self.doc_freqs[term] = 0
                self.doc_freqs[term] += 1

        self.avgdl = sum(self.doc_len) / self.doc_count if self.doc_count > 0 else 0
        self._calc_idf()

    def _calc_idf(self):
        """计算 IDF"""
        idf_sum = 0
        negative_idfs = []

        for term, freq in self.doc_freqs.items():
            idf = math.log(self.doc_count - freq + 0.5) - math.log(freq + 0.5)
            self.idf[term] = idf
            idf_sum += idf
            if idf < 0:
                negative_idfs.append(term)

        avg_idf = idf_sum / len(self.idf) if self.idf else 0
        eps = self.epsilon * avg_idf

        for term in negative_idfs:
            self.idf[term] = eps

    def get_scores(self, query: str) -> list[float]:
        """计算查询与所有文档的 BM25 分数"""
        query_tokens = self._tokenize(query)
        scores = []

        for i, doc_term_freq in enumerate(self.doc_term_freqs):
            score = 0
            doc_len = self.doc_len[i]

            for token in query_tokens:
                if token not in doc_term_freq:
                    continue

                tf = doc_term_freq[token]
                idf = self.idf.get(token, 0)

                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (
                    1 - self.b + self.b * doc_len / self.avgdl
                )
                score += idf * numerator / denominator

            scores.append(score)

        return scores

    def search(self, query: str, k: int = 5) -> list[tuple[Document, float]]:
        """搜索相关文档"""
        scores = self.get_scores(query)

        scored_docs = list(zip(self.documents, scores, strict=False))
        scored_docs.sort(key=lambda x: x[1], reverse=True)

        return scored_docs[:k]


class HybridRetriever:
    """混合检索器

    结合关键词检索（BM25）和语义检索（向量检索）。
    支持多种融合策略：
    - weighted: 加权融合
    - rrf: Reciprocal Rank Fusion
    - score: 分数归一化融合
    """

    def __init__(
        self,
        fusion_method: str = "rrf",
        keyword_weight: float = 0.3,
        semantic_weight: float = 0.7,
        rrf_k: int = 60,
    ):
        """
        初始化混合检索器

        Args:
            fusion_method: 融合方法 (weighted/rrf/score)
            keyword_weight: 关键词检索权重
            semantic_weight: 语义检索权重
            rrf_k: RRF 算法的 k 参数
        """
        self.fusion_method = fusion_method
        self.keyword_weight = keyword_weight
        self.semantic_weight = semantic_weight
        self.rrf_k = rrf_k
        self.bm25 = BM25()
        self.documents: list[Document] = []

    def fit(self, documents: list[Document]):
        """训练 BM25 模型"""
        self.documents = documents
        self.bm25.fit(documents)

    def retrieve(
        self,
        query: str,
        vector_store,
        k: int = 5,
        alpha: float | None = None,
    ) -> list[tuple[Document, float]]:
        """
        混合检索

        Args:
            query: 查询文本
            vector_store: 向量存储
            k: 返回文档数量
            alpha: 关键词权重（可选，覆盖默认值）

        Returns:
            (文档, 分数) 列表
        """
        keyword_weight = alpha if alpha is not None else self.keyword_weight
        semantic_weight = 1 - keyword_weight

        keyword_results = self.bm25.search(query, k * 2)

        semantic_results = vector_store.similarity_search_with_score(query, k=k * 2)

        if self.fusion_method == "weighted":
            return self._weighted_fusion(
                keyword_results, semantic_results, k, keyword_weight, semantic_weight
            )
        elif self.fusion_method == "rrf":
            return self._rrf_fusion(keyword_results, semantic_results, k)
        else:
            return self._score_fusion(
                keyword_results, semantic_results, k, keyword_weight, semantic_weight
            )

    def _weighted_fusion(
        self,
        keyword_results: list[tuple[Document, float]],
        semantic_results: list[tuple[Document, float]],
        k: int,
        keyword_weight: float,
        semantic_weight: float,
    ) -> list[tuple[Document, float]]:
        """加权融合"""
        doc_scores: dict[str, tuple[Document, float]] = {}

        max_kw_score = max((score for _, score in keyword_results), default=1.0) or 1.0
        for doc, score in keyword_results:
            doc_id = self._get_doc_id(doc)
            normalized_score = score / max_kw_score
            doc_scores[doc_id] = (doc, normalized_score * keyword_weight)

        max_sem_score = (
            max((score for _, score in semantic_results), default=1.0) or 1.0
        )
        for doc, score in semantic_results:
            doc_id = self._get_doc_id(doc)
            normalized_score = 1 - (score / max_sem_score)
            if doc_id in doc_scores:
                existing_doc, existing_score = doc_scores[doc_id]
                doc_scores[doc_id] = (
                    existing_doc,
                    existing_score + normalized_score * semantic_weight,
                )
            else:
                doc_scores[doc_id] = (doc, normalized_score * semantic_weight)

        results = sorted(doc_scores.values(), key=lambda x: x[1], reverse=True)
        return results[:k]

    def _rrf_fusion(
        self,
        keyword_results: list[tuple[Document, float]],
        semantic_results: list[tuple[Document, float]],
        k: int,
    ) -> list[tuple[Document, float]]:
        """Reciprocal Rank Fusion"""
        doc_scores: dict[str, tuple[Document, float]] = {}

        for rank, (doc, _) in enumerate(keyword_results):
            doc_id = self._get_doc_id(doc)
            rrf_score = 1 / (self.rrf_k + rank + 1)
            doc_scores[doc_id] = (doc, rrf_score)

        for rank, (doc, _) in enumerate(semantic_results):
            doc_id = self._get_doc_id(doc)
            rrf_score = 1 / (self.rrf_k + rank + 1)
            if doc_id in doc_scores:
                existing_doc, existing_score = doc_scores[doc_id]
                doc_scores[doc_id] = (existing_doc, existing_score + rrf_score)
            else:
                doc_scores[doc_id] = (doc, rrf_score)

        results = sorted(doc_scores.values(), key=lambda x: x[1], reverse=True)
        return results[:k]

    def _score_fusion(
        self,
        keyword_results: list[tuple[Document, float]],
        semantic_results: list[tuple[Document, float]],
        k: int,
        keyword_weight: float,
        semantic_weight: float,
    ) -> list[tuple[Document, float]]:
        """分数归一化融合"""
        doc_scores: dict[str, tuple[Document, float]] = {}

        kw_scores = [score for _, score in keyword_results]
        kw_min = min(kw_scores) if kw_scores else 0
        kw_max = max(kw_scores) if kw_scores else 1
        kw_range = kw_max - kw_min if kw_max != kw_min else 1

        for doc, score in keyword_results:
            doc_id = self._get_doc_id(doc)
            normalized = (score - kw_min) / kw_range if kw_range > 0 else 0.5
            doc_scores[doc_id] = (doc, normalized * keyword_weight)

        sem_scores = [score for _, score in semantic_results]
        sem_min = min(sem_scores) if sem_scores else 0
        sem_max = max(sem_scores) if sem_scores else 1
        sem_range = sem_max - sem_min if sem_max != sem_min else 1

        for doc, score in semantic_results:
            doc_id = self._get_doc_id(doc)
            normalized = 1 - (score - sem_min) / sem_range if sem_range > 0 else 0.5
            if doc_id in doc_scores:
                existing_doc, existing_score = doc_scores[doc_id]
                doc_scores[doc_id] = (
                    existing_doc,
                    existing_score + normalized * semantic_weight,
                )
            else:
                doc_scores[doc_id] = (doc, normalized * semantic_weight)

        results = sorted(doc_scores.values(), key=lambda x: x[1], reverse=True)
        return results[:k]

    def _get_doc_id(self, doc: Document) -> str:
        """获取文档唯一标识"""
        if "source" in doc.metadata:
            return f"{doc.metadata['source']}:{hash(doc.page_content[:100])}"
        return str(hash(doc.page_content[:100]))


class HybridRAGSystem:
    """混合 RAG 系统

    结合关键词检索和语义检索的 RAG 系统。
    """

    def __init__(
        self,
        rag_system,
        fusion_method: str = "rrf",
        keyword_weight: float = 0.3,
    ):
        """
        初始化混合 RAG 系统

        Args:
            rag_system: 基础 RAG 系统
            fusion_method: 融合方法
            keyword_weight: 关键词权重
        """
        self.rag = rag_system
        self.retriever = HybridRetriever(
            fusion_method=fusion_method,
            keyword_weight=keyword_weight,
        )
        self._fitted = False

    def fit(self):
        """训练混合检索模型"""
        if not self.rag.vector_store:
            raise ValueError("RAG 系统的向量存储未初始化")

        if hasattr(self.rag.vector_store, "similarity_search"):
            docs = self.rag.vector_store.similarity_search("", k=1000)
            self.retriever.fit(docs)
            self._fitted = True

    def retrieve(
        self,
        query: str,
        k: int = 5,
        alpha: float | None = None,
    ) -> list[tuple[Document, float]]:
        """
        混合检索

        Args:
            query: 查询文本
            k: 返回文档数量
            alpha: 关键词权重

        Returns:
            (文档, 分数) 列表
        """
        if not self._fitted:
            self.fit()

        return self.retriever.retrieve(
            query=query,
            vector_store=self.rag.vector_store,
            k=k,
            alpha=alpha,
        )

    def generate_answer(
        self,
        query: str,
        k: int = 3,
        alpha: float | None = None,
        max_context_length: int = 4000,
    ):
        """
        生成回答

        Args:
            query: 查询文本
            k: 检索文档数量
            alpha: 关键词权重
            max_context_length: 最大上下文长度

        Returns:
            (回答, 相关文档列表)
        """
        results = self.retrieve(query, k, alpha)
        relevant_docs = [doc for doc, _ in results]

        if not relevant_docs:
            return "抱歉，没有找到相关的文档信息。", []

        prompt = self.rag.prompt_builder.build_qa_prompt(
            query=query,
            documents=relevant_docs,
            max_context_length=max_context_length,
        )

        answer = self.rag.llm_integration.generate(prompt)
        return answer, relevant_docs
