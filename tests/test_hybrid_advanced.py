import unittest
from unittest.mock import MagicMock

from langchain_core.documents import Document


class TestHybridRAGSystem(unittest.TestCase):
    """测试 HybridRAGSystem"""

    def test_init(self):
        """测试初始化"""
        from langchain_llm_toolkit.hybrid_retriever import HybridRAGSystem

        mock_rag = MagicMock()
        system = HybridRAGSystem(mock_rag)

        self.assertEqual(system.rag, mock_rag)
        self.assertFalse(system._fitted)

    def test_fit(self):
        """测试训练"""
        from langchain_llm_toolkit.hybrid_retriever import HybridRAGSystem

        mock_rag = MagicMock()
        mock_rag.vector_store = MagicMock()
        mock_rag.vector_store.similarity_search.return_value = [
            Document(page_content="test", metadata={})
        ]

        system = HybridRAGSystem(mock_rag)
        system.fit()

        self.assertTrue(system._fitted)

    def test_fit_no_vector_store(self):
        """测试训练时没有向量存储"""
        from langchain_llm_toolkit.hybrid_retriever import HybridRAGSystem

        mock_rag = MagicMock()
        mock_rag.vector_store = None

        system = HybridRAGSystem(mock_rag)

        with self.assertRaises(ValueError):
            system.fit()

    def test_retrieve_auto_fit(self):
        """测试检索时自动训练"""
        from langchain_llm_toolkit.hybrid_retriever import HybridRAGSystem

        mock_rag = MagicMock()
        mock_rag.vector_store = MagicMock()
        mock_rag.vector_store.similarity_search.return_value = [
            Document(page_content="test doc", metadata={"source": "test.txt"})
        ]

        system = HybridRAGSystem(mock_rag)
        system.retrieve("test query", k=1)

        self.assertTrue(system._fitted)


class TestBM25Advanced(unittest.TestCase):
    """测试 BM25 高级功能"""

    def test_doc_length_normalization(self):
        """测试文档长度归一化"""
        from langchain_llm_toolkit.hybrid_retriever import BM25

        bm25 = BM25()
        docs = [
            Document(page_content="短文档"),
            Document(page_content="这是一个比较长的文档内容用于测试"),
        ]
        bm25.fit(docs)

        self.assertGreater(bm25.avgdl, 0)

    def test_search_with_no_results(self):
        """测试无结果搜索"""
        from langchain_llm_toolkit.hybrid_retriever import BM25

        bm25 = BM25()
        docs = [Document(page_content="Python 编程")]
        bm25.fit(docs)

        results = bm25.search("完全不相关的内容xyz", k=1)
        self.assertEqual(len(results), 1)


class TestHybridRetrieverAdvanced(unittest.TestCase):
    """测试 HybridRetriever 高级功能"""

    def test_weighted_fusion_search(self):
        """测试加权融合搜索"""
        from langchain_llm_toolkit.hybrid_retriever import HybridRetriever

        docs = [
            Document(page_content="Python 编程语言", metadata={"id": "1"}),
            Document(page_content="Java 编程语言", metadata={"id": "2"}),
        ]

        retriever = HybridRetriever(fusion_method="weighted")
        retriever.fit(docs)

        self.assertEqual(retriever.fusion_method, "weighted")

    def test_score_normalization(self):
        """测试分数归一化"""
        from langchain_llm_toolkit.hybrid_retriever import HybridRetriever

        docs = [
            Document(page_content="测试文档一", metadata={"id": "1"}),
            Document(page_content="测试文档二", metadata={"id": "2"}),
        ]

        retriever = HybridRetriever(fusion_method="score")
        retriever.fit(docs)

        self.assertEqual(retriever.fusion_method, "score")

    def test_custom_weights(self):
        """测试自定义权重"""
        from langchain_llm_toolkit.hybrid_retriever import HybridRetriever

        retriever = HybridRetriever(
            keyword_weight=0.7,
            semantic_weight=0.3,
        )

        self.assertEqual(retriever.keyword_weight, 0.7)
        self.assertEqual(retriever.semantic_weight, 0.3)


if __name__ == "__main__":
    unittest.main()
