import unittest
import os
import tempfile
import shutil
from unittest.mock import patch, Mock
from rag import RAGSystem
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
import numpy as np
from typing import List


class MockEmbeddings(Embeddings):
    """Mock embeddings for testing"""

    def __init__(self):
        pass

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Mock embed documents"""
        return [np.random.rand(1536).tolist() for _ in texts]

    def embed_query(self, text: str) -> List[float]:
        """Mock embed query"""
        result: List[float] = np.random.rand(1536).tolist()
        return result


@unittest.skip("Qdrant 本地模式不支持并发测试，请在实际使用中测试")
class TestRAGSystemQdrant(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.test_txt_file = os.path.join(self.temp_dir, "test.txt")

        with open(self.test_txt_file, "w", encoding="utf-8") as f:
            f.write("LangChain 是一个用于开发基于语言模型的应用程序的框架。\n\n")
            f.write("它提供了一系列工具和组件，使得开发者可以更轻松地构建复杂的 LLM 应用。")

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def _create_rag_system(self):
        """创建独立的 RAG 系统实例"""
        qdrant_dir = os.path.join(self.temp_dir, f"qdrant_{self._testMethodName}")
        rag_system = RAGSystem(vector_store_type="qdrant")
        rag_system.qdrant_persist_dir = qdrant_dir
        rag_system.embeddings = MockEmbeddings()
        return rag_system

    def test_setup_embeddings(self):
        """测试设置嵌入模型"""
        rag_system = self._create_rag_system()
        with patch.object(rag_system, "setup_embeddings") as mock_setup:
            mock_embeddings = MockEmbeddings()
            mock_setup.return_value = mock_embeddings
            embeddings = rag_system.setup_embeddings()
            self.assertIsNotNone(embeddings)

    def test_create_vector_store(self):
        """测试创建向量存储"""
        rag_system = self._create_rag_system()
        test_doc = Document(page_content="测试文档内容", metadata={"source": "test.txt"})

        vector_store = rag_system.create_vector_store([test_doc])
        self.assertIsNotNone(vector_store)

    def test_add_documents(self):
        """测试向向量存储添加文档"""
        rag_system = self._create_rag_system()
        test_doc1 = Document(page_content="测试文档1", metadata={"source": "test1.txt"})
        rag_system.create_vector_store([test_doc1])

        test_doc2 = Document(page_content="测试文档2", metadata={"source": "test2.txt"})
        vector_store = rag_system.add_documents([test_doc2])
        self.assertIsNotNone(vector_store)

    def test_add_documents_without_vector_store(self):
        """测试在向量存储未初始化时添加文档"""
        rag_system = self._create_rag_system()
        test_doc = Document(page_content="测试文档", metadata={"source": "test.txt"})

        with self.assertRaises(ValueError):
            rag_system.add_documents([test_doc])

    def test_retrieve_documents(self):
        """测试检索文档"""
        rag_system = self._create_rag_system()
        test_doc = Document(page_content="测试文档内容", metadata={"source": "test.txt"})
        rag_system.create_vector_store([test_doc])

        results = rag_system.retrieve_documents("测试")
        self.assertGreater(len(results), 0)

    def test_retrieve_documents_without_vector_store(self):
        """测试在向量存储未初始化时检索文档"""
        rag_system = self._create_rag_system()
        with self.assertRaises(ValueError):
            rag_system.retrieve_documents("测试")

    def test_retrieve_documents_with_scores(self):
        """测试带分数的检索文档"""
        rag_system = self._create_rag_system()
        test_doc = Document(page_content="测试文档内容", metadata={"source": "test.txt"})
        rag_system.create_vector_store([test_doc])

        results = rag_system.retrieve_documents_with_scores("测试")
        self.assertGreater(len(results), 0)
        doc, score = results[0]
        self.assertIsInstance(doc, Document)
        self.assertIsInstance(score, (int, float))

    @patch("llm_integration.LLMIntegration.generate")
    def test_generate_answer(self, mock_generate):
        """测试生成回答"""
        mock_generate.return_value = "测试回答"

        rag_system = self._create_rag_system()
        test_doc = Document(page_content="测试文档内容", metadata={"source": "test.txt"})
        rag_system.create_vector_store([test_doc])

        answer, relevant_docs = rag_system.generate_answer("测试")
        self.assertEqual(answer, "测试回答")
        self.assertGreater(len(relevant_docs), 0)

    def test_load_and_process_documents(self):
        """测试加载和处理文档"""
        rag_system = self._create_rag_system()
        documents = rag_system.load_and_process_documents([self.test_txt_file])
        self.assertGreater(len(documents), 0)

    def test_save_vector_store(self):
        """测试保存向量存储"""
        rag_system = self._create_rag_system()
        test_doc = Document(page_content="测试文档内容", metadata={"source": "test.txt"})
        rag_system.create_vector_store([test_doc])

        save_path = os.path.join(self.temp_dir, "vector_store")
        result = rag_system.save_vector_store(save_path)
        self.assertTrue(result)

    def test_save_vector_store_without_vector_store(self):
        """测试在向量存储未初始化时保存"""
        rag_system = self._create_rag_system()
        with self.assertRaises(ValueError):
            rag_system.save_vector_store("vector_store")

    def test_get_collection_info(self):
        """测试获取集合信息"""
        rag_system = self._create_rag_system()
        test_doc = Document(page_content="测试文档内容", metadata={"source": "test.txt"})
        rag_system.create_vector_store([test_doc])

        info = rag_system.get_collection_info()
        self.assertIn("points_count", info)

    def test_delete_collection(self):
        """测试删除集合"""
        rag_system = self._create_rag_system()
        test_doc = Document(page_content="测试文档内容", metadata={"source": "test.txt"})
        rag_system.create_vector_store([test_doc])

        rag_system.delete_collection()


class TestRAGSystemFAISS(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.test_txt_file = os.path.join(self.temp_dir, "test.txt")

        with open(self.test_txt_file, "w", encoding="utf-8") as f:
            f.write("测试文档内容")

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def _create_rag_system(self):
        """创建独立的 RAG 系统实例"""
        rag_system = RAGSystem(vector_store_type="faiss")
        rag_system.embeddings = MockEmbeddings()
        return rag_system

    def test_create_vector_store_faiss(self):
        """测试创建 FAISS 向量存储"""
        rag_system = self._create_rag_system()
        test_doc = Document(page_content="测试文档内容", metadata={"source": "test.txt"})

        vector_store = rag_system.create_vector_store([test_doc])
        self.assertIsNotNone(vector_store)

    def test_get_collection_info_faiss(self):
        """测试 FAISS 集合信息"""
        rag_system = self._create_rag_system()
        test_doc = Document(page_content="测试文档内容", metadata={"source": "test.txt"})
        rag_system.create_vector_store([test_doc])

        info = rag_system.get_collection_info()
        self.assertEqual(info["type"], "FAISS")

    def test_add_documents_faiss(self):
        """测试添加文档到 FAISS"""
        rag_system = self._create_rag_system()
        test_doc = Document(page_content="初始文档", metadata={"source": "test1.txt"})
        rag_system.create_vector_store([test_doc])

        new_doc = Document(page_content="新文档", metadata={"source": "test2.txt"})
        rag_system.add_documents([new_doc])

        results = rag_system.retrieve_documents("文档", k=2)
        self.assertGreater(len(results), 0)

    def test_add_documents_without_vector_store(self):
        """测试在向量存储未初始化时添加文档"""
        rag_system = self._create_rag_system()
        test_doc = Document(page_content="测试", metadata={"source": "test.txt"})

        with self.assertRaises(ValueError) as context:
            rag_system.add_documents([test_doc])
        self.assertIn("向量存储未初始化", str(context.exception))

    def test_retrieve_documents_faiss(self):
        """测试 FAISS 检索文档"""
        rag_system = self._create_rag_system()
        test_doc = Document(page_content="Python 是一种编程语言", metadata={"source": "test.txt"})
        rag_system.create_vector_store([test_doc])

        results = rag_system.retrieve_documents("编程语言", k=1)
        self.assertEqual(len(results), 1)
        self.assertIsInstance(results[0], Document)

    def test_retrieve_documents_without_vector_store(self):
        """测试在向量存储未初始化时检索文档"""
        rag_system = self._create_rag_system()

        with self.assertRaises(ValueError) as context:
            rag_system.retrieve_documents("测试")
        self.assertIn("向量存储未初始化", str(context.exception))

    def test_retrieve_documents_with_scores_faiss(self):
        """测试 FAISS 带分数的检索"""
        rag_system = self._create_rag_system()
        test_doc = Document(page_content="测试文档", metadata={"source": "test.txt"})
        rag_system.create_vector_store([test_doc])

        results = rag_system.retrieve_documents_with_scores("测试", k=1)
        self.assertEqual(len(results), 1)
        doc, score = results[0]
        self.assertIsInstance(doc, Document)
        self.assertIsInstance(float(score), (int, float))

    @patch("rag.LLMIntegration")
    def test_generate_summary(self, mock_llm_class):
        """测试生成摘要"""
        mock_llm = Mock()
        mock_llm.generate.return_value = "这是文档摘要"
        mock_llm_class.return_value = mock_llm

        rag_system = self._create_rag_system()
        test_doc = Document(page_content="长文档内容" * 100, metadata={"source": "test.txt"})

        summary = rag_system.generate_summary([test_doc])
        self.assertEqual(summary, "这是文档摘要")
        mock_llm.generate.assert_called_once()

    @patch("rag.LLMIntegration")
    def test_extract_information(self, mock_llm_class):
        """测试信息提取"""
        mock_llm = Mock()
        mock_llm.generate.return_value = "提取的关键信息"
        mock_llm_class.return_value = mock_llm

        rag_system = self._create_rag_system()
        test_doc = Document(page_content="包含关键信息的文档", metadata={"source": "test.txt"})

        result = rag_system.extract_information([test_doc], "关键信息")
        self.assertEqual(result, "提取的关键信息")
        mock_llm.generate.assert_called_once()

    def test_load_vector_store_faiss(self):
        """测试加载 FAISS 向量存储"""
        rag_system = self._create_rag_system()
        test_doc = Document(page_content="测试文档", metadata={"source": "test.txt"})
        rag_system.create_vector_store([test_doc])

        save_path = os.path.join(self.temp_dir, "faiss_store")
        rag_system.save_vector_store(save_path)

        rag_system2 = self._create_rag_system()
        rag_system2.load_vector_store(save_path)

        results = rag_system2.retrieve_documents("测试", k=1)
        self.assertEqual(len(results), 1)

    def test_load_vector_store_without_embeddings(self):
        """测试在未设置 embeddings 时加载向量存储会自动初始化"""
        rag_system = self._create_rag_system()
        save_path = os.path.join(self.temp_dir, "faiss_store")

        # 先创建并保存一个向量存储
        test_doc = Document(page_content="测试文档", metadata={"source": "test.txt"})
        rag_system.create_vector_store([test_doc])
        rag_system.save_vector_store(save_path)

        # 创建新的 RAG 系统，不设置 embeddings
        rag_system2 = RAGSystem(vector_store_type="faiss")
        self.assertIsNone(rag_system2.embeddings)

        # 使用 MockEmbeddings 加载向量存储
        rag_system2.embeddings = MockEmbeddings()
        rag_system2.load_vector_store(save_path)
        self.assertIsNotNone(rag_system2.vector_store)

    def test_setup_embeddings(self):
        """测试设置 embeddings"""
        if not os.getenv("OPENAI_API_KEY"):
            self.skipTest("需要 OPENAI_API_KEY 环境变量")

        rag_system = RAGSystem(vector_store_type="faiss")
        self.assertIsNone(rag_system.embeddings)

        embeddings = rag_system.setup_embeddings()
        self.assertIsNotNone(embeddings)
        self.assertIsNotNone(rag_system.embeddings)

    def test_delete_collection_faiss(self):
        """测试删除 FAISS 集合（FAISS 不支持删除集合）"""
        rag_system = self._create_rag_system()
        test_doc = Document(page_content="测试文档", metadata={"source": "test.txt"})
        rag_system.create_vector_store([test_doc])

        # FAISS 不支持删除集合，调用 delete_collection 不应该报错
        rag_system.delete_collection()
        # vector_store 应该仍然存在
        self.assertIsNotNone(rag_system.vector_store)

    def test_multiple_documents(self):
        """测试处理多个文档"""
        rag_system = self._create_rag_system()

        docs = [
            Document(page_content="文档1：Python 编程", metadata={"source": "doc1.txt"}),
            Document(page_content="文档2：Java 编程", metadata={"source": "doc2.txt"}),
            Document(page_content="文档3：JavaScript 编程", metadata={"source": "doc3.txt"}),
        ]

        rag_system.create_vector_store(docs)
        results = rag_system.retrieve_documents("编程", k=3)
        self.assertEqual(len(results), 3)

    def test_empty_documents(self):
        """测试空文档列表"""
        rag_system = self._create_rag_system()

        with self.assertRaises(Exception):
            rag_system.create_vector_store([])

    def test_large_document(self):
        """测试大文档处理"""
        rag_system = self._create_rag_system()

        large_content = "测试内容 " * 10000
        test_doc = Document(page_content=large_content, metadata={"source": "large.txt"})

        vector_store = rag_system.create_vector_store([test_doc])
        self.assertIsNotNone(vector_store)

    def test_metadata_preservation(self):
        """测试元数据保留"""
        rag_system = self._create_rag_system()

        test_doc = Document(
            page_content="测试内容",
            metadata={
                "source": "test.txt",
                "author": "测试作者",
                "date": "2024-01-01",
                "category": "测试",
            },
        )

        rag_system.create_vector_store([test_doc])
        results = rag_system.retrieve_documents("测试", k=1)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].metadata["source"], "test.txt")
        self.assertEqual(results[0].metadata["author"], "测试作者")

    @patch("rag.LLMIntegration")
    def test_generate_answer_with_different_k(self, mock_llm_class):
        """测试不同 k 值的答案生成"""
        mock_llm = Mock()
        mock_llm.generate.return_value = "测试回答"
        mock_llm_class.return_value = mock_llm

        rag_system = self._create_rag_system()

        docs = [
            Document(page_content=f"文档{i}", metadata={"source": f"doc{i}.txt"}) for i in range(5)
        ]

        rag_system.create_vector_store(docs)

        for k in [1, 3, 5]:
            answer, relevant_docs = rag_system.generate_answer("测试", k=k)
            self.assertEqual(answer, "测试回答")
            self.assertLessEqual(len(relevant_docs), k)


if __name__ == "__main__":
    unittest.main()
