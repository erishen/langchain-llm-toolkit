import pytest
from langchain_core.documents import Document
from langchain_llm_toolkit.hybrid_retriever import BM25, HybridRetriever


class TestBM25:
    """测试 BM25 关键词检索"""

    @pytest.fixture
    def sample_documents(self):
        return [
            Document(page_content="Python 是一种流行的编程语言，广泛用于数据科学和机器学习。"),
            Document(page_content="JavaScript 是网页开发的主要语言，用于前端和后端开发。"),
            Document(page_content="机器学习是人工智能的一个分支，使用算法从数据中学习。"),
            Document(page_content="深度学习是机器学习的子领域，使用神经网络进行学习。"),
            Document(page_content="自然语言处理是 AI 的重要应用，用于理解和生成人类语言。"),
        ]

    @pytest.fixture
    def bm25(self, sample_documents):
        bm25 = BM25()
        bm25.fit(sample_documents)
        return bm25

    def test_fit(self, sample_documents):
        """测试训练 BM25 模型"""
        bm25 = BM25()
        bm25.fit(sample_documents)

        assert bm25.doc_count == 5
        assert bm25.avgdl > 0
        assert len(bm25.doc_term_freqs) == 5

    def test_search(self, bm25):
        """测试搜索功能"""
        results = bm25.search("机器学习", k=3)

        assert len(results) == 3
        assert all(isinstance(doc, Document) for doc, score in results)
        assert all(score >= 0 for doc, score in results)

    def test_search_relevance(self, bm25):
        """测试搜索相关性"""
        results = bm25.search("机器学习", k=5)

        top_doc = results[0][0]
        assert "机器学习" in top_doc.page_content

    def test_search_empty_query(self, bm25):
        """测试空查询"""
        results = bm25.search("", k=3)
        assert len(results) <= 3

    def test_get_scores(self, bm25):
        """测试获取分数"""
        scores = bm25.get_scores("Python")

        assert len(scores) == 5
        assert any(score > 0 for score in scores)

    def test_tokenize_chinese(self):
        """测试中文分词"""
        bm25 = BM25()
        tokens = bm25._tokenize("Python 编程语言")

        assert "python" in tokens
        assert "编程语言" in tokens


class TestHybridRetriever:
    """测试混合检索器"""

    @pytest.fixture
    def sample_documents(self):
        return [
            Document(
                page_content="Python 是一种流行的编程语言。",
                metadata={"source": "doc1.txt"},
            ),
            Document(
                page_content="JavaScript 用于网页开发。",
                metadata={"source": "doc2.txt"},
            ),
            Document(page_content="机器学习是 AI 的分支。", metadata={"source": "doc3.txt"}),
        ]

    @pytest.fixture
    def retriever(self, sample_documents):
        retriever = HybridRetriever(fusion_method="rrf")
        retriever.fit(sample_documents)
        return retriever

    def test_fit(self, sample_documents):
        """测试训练"""
        retriever = HybridRetriever()
        retriever.fit(sample_documents)

        assert retriever.documents == sample_documents
        assert retriever.bm25.doc_count == 3

    def test_weighted_fusion(self, sample_documents):
        """测试加权融合"""
        retriever = HybridRetriever(fusion_method="weighted")
        retriever.fit(sample_documents)

        assert retriever.fusion_method == "weighted"

    def test_rrf_fusion(self, sample_documents):
        """测试 RRF 融合"""
        retriever = HybridRetriever(fusion_method="rrf")
        retriever.fit(sample_documents)

        assert retriever.fusion_method == "rrf"

    def test_score_fusion(self, sample_documents):
        """测试分数融合"""
        retriever = HybridRetriever(fusion_method="score")
        retriever.fit(sample_documents)

        assert retriever.fusion_method == "score"

    def test_get_doc_id(self, retriever):
        """测试文档 ID 生成"""
        doc = Document(page_content="测试内容", metadata={"source": "test.txt"})
        doc_id = retriever._get_doc_id(doc)

        assert isinstance(doc_id, str)
        assert len(doc_id) > 0

    def test_different_weights(self, sample_documents):
        """测试不同权重"""
        retriever = HybridRetriever(
            keyword_weight=0.5,
            semantic_weight=0.5,
        )
        retriever.fit(sample_documents)

        assert retriever.keyword_weight == 0.5
        assert retriever.semantic_weight == 0.5

    def test_rrf_k_parameter(self, sample_documents):
        """测试 RRF K 参数"""
        retriever = HybridRetriever(rrf_k=100)
        retriever.fit(sample_documents)

        assert retriever.rrf_k == 100


class TestBM25EdgeCases:
    """测试 BM25 边界情况"""

    def test_single_document(self):
        """测试单个文档"""
        bm25 = BM25()
        docs = [Document(page_content="这是唯一的文档")]
        bm25.fit(docs)

        results = bm25.search("文档", k=1)
        assert len(results) == 1

    def test_duplicate_documents(self):
        """测试重复文档"""
        bm25 = BM25()
        docs = [
            Document(page_content="重复内容"),
            Document(page_content="重复内容"),
        ]
        bm25.fit(docs)

        results = bm25.search("重复", k=2)
        assert len(results) == 2

    def test_special_characters(self):
        """测试特殊字符"""
        bm25 = BM25()
        docs = [Document(page_content="包含特殊字符 !@#$%^&*()")]
        bm25.fit(docs)

        results = bm25.search("特殊", k=1)
        assert len(results) == 1

    def test_very_long_document(self):
        """测试超长文档"""
        bm25 = BM25()
        long_text = "Python " * 1000
        docs = [Document(page_content=long_text)]
        bm25.fit(docs)

        results = bm25.search("Python", k=1)
        assert len(results) == 1

    def test_numbers_in_query(self):
        """测试数字查询"""
        bm25 = BM25()
        docs = [Document(page_content="版本 3.11 发布")]
        bm25.fit(docs)

        results = bm25.search("3.11", k=1)
        assert len(results) == 1
