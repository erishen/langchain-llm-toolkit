import unittest
from unittest.mock import patch, MagicMock


class TestOllamaEmbeddingsWrapper(unittest.TestCase):
    """测试 OllamaEmbeddingsWrapper"""

    def test_init_default_params(self):
        """测试默认参数初始化"""
        mock_ollama = MagicMock()
        mock_client = MagicMock()
        mock_ollama.Client.return_value = mock_client

        with patch.dict("sys.modules", {"ollama": mock_ollama}):
            from langchain_llm_toolkit.rag import OllamaEmbeddingsWrapper

            wrapper = OllamaEmbeddingsWrapper()

            self.assertEqual(wrapper.model, "nomic-embed-text")
            self.assertEqual(wrapper.num_ctx, 8192)
            self.assertTrue(wrapper._use_options)

    def test_init_custom_params(self):
        """测试自定义参数初始化"""
        mock_ollama = MagicMock()
        mock_client = MagicMock()
        mock_ollama.Client.return_value = mock_client

        with patch.dict("sys.modules", {"ollama": mock_ollama}):
            from langchain_llm_toolkit.rag import OllamaEmbeddingsWrapper

            wrapper = OllamaEmbeddingsWrapper(
                model="snowflake-arctic-embed2", base_url="http://custom:11434", num_ctx=4096
            )

            self.assertEqual(wrapper.model, "snowflake-arctic-embed2")
            self.assertEqual(wrapper.base_url, "http://custom:11434")
            self.assertEqual(wrapper.num_ctx, 4096)
            self.assertFalse(wrapper._use_options)

    def test_embed_documents_with_options(self):
        """测试嵌入文档（带 options）"""
        mock_ollama = MagicMock()
        mock_client = MagicMock()
        mock_client.embeddings.return_value = {"embedding": [0.1, 0.2, 0.3]}
        mock_ollama.Client.return_value = mock_client

        with patch.dict("sys.modules", {"ollama": mock_ollama}):
            from langchain_llm_toolkit.rag import OllamaEmbeddingsWrapper

            wrapper = OllamaEmbeddingsWrapper(model="nomic-embed-text")
            result = wrapper.embed_documents(["text1", "text2"])

            self.assertEqual(len(result), 2)
            self.assertEqual(result[0], [0.1, 0.2, 0.3])
            self.assertEqual(mock_client.embeddings.call_count, 2)

    def test_embed_documents_without_options(self):
        """测试嵌入文档（不带 options）"""
        mock_ollama = MagicMock()
        mock_client = MagicMock()
        mock_client.embeddings.return_value = {"embedding": [0.1, 0.2, 0.3]}
        mock_ollama.Client.return_value = mock_client

        with patch.dict("sys.modules", {"ollama": mock_ollama}):
            from langchain_llm_toolkit.rag import OllamaEmbeddingsWrapper

            wrapper = OllamaEmbeddingsWrapper(model="snowflake-arctic-embed2")
            result = wrapper.embed_documents(["text1"])

            self.assertEqual(len(result), 1)
            mock_client.embeddings.assert_called_once()

    def test_embed_query_with_options(self):
        """测试嵌入查询（带 options）"""
        mock_ollama = MagicMock()
        mock_client = MagicMock()
        mock_client.embeddings.return_value = {"embedding": [0.1, 0.2, 0.3]}
        mock_ollama.Client.return_value = mock_client

        with patch.dict("sys.modules", {"ollama": mock_ollama}):
            from langchain_llm_toolkit.rag import OllamaEmbeddingsWrapper

            wrapper = OllamaEmbeddingsWrapper(model="nomic-embed-text")
            result = wrapper.embed_query("test query")

            self.assertEqual(result, [0.1, 0.2, 0.3])
            mock_client.embeddings.assert_called_once()

    def test_embed_query_without_options(self):
        """测试嵌入查询（不带 options）"""
        mock_ollama = MagicMock()
        mock_client = MagicMock()
        mock_client.embeddings.return_value = {"embedding": [0.4, 0.5, 0.6]}
        mock_ollama.Client.return_value = mock_client

        with patch.dict("sys.modules", {"ollama": mock_ollama}):
            from langchain_llm_toolkit.rag import OllamaEmbeddingsWrapper

            wrapper = OllamaEmbeddingsWrapper(model="snowflake-arctic-embed2")
            result = wrapper.embed_query("test query")

            self.assertEqual(result, [0.4, 0.5, 0.6])
            mock_client.embeddings.assert_called_once()


class TestRAGSystemInit(unittest.TestCase):
    """测试 RAGSystem 初始化"""

    def test_init_default_params(self):
        """测试默认参数初始化"""
        from langchain_llm_toolkit.rag import RAGSystem

        rag = RAGSystem()

        self.assertEqual(rag.vector_store_type, "qdrant")
        self.assertEqual(rag.embedding_type, "ollama")
        self.assertEqual(rag.embedding_model, "snowflake-arctic-embed2")
        self.assertEqual(rag.llm_model, "ollama/gemma4")
        self.assertIsNone(rag.vector_store)
        self.assertIsNone(rag.embeddings)

    def test_init_custom_params(self):
        """测试自定义参数初始化"""
        from langchain_llm_toolkit.rag import RAGSystem

        rag = RAGSystem(
            vector_store_type="faiss",
            embedding_type="openai",
            embedding_model="text-embedding-3-small",
            llm_model="gpt-4o",
        )

        self.assertEqual(rag.vector_store_type, "faiss")
        self.assertEqual(rag.embedding_type, "openai")
        self.assertEqual(rag.embedding_model, "text-embedding-3-small")
        self.assertEqual(rag.llm_model, "gpt-4o")


class TestRAGSystemSetupEmbeddings(unittest.TestCase):
    """测试 RAGSystem embeddings 设置"""

    @patch("langchain_llm_toolkit.rag.OllamaEmbeddingsWrapper")
    def test_setup_embeddings_ollama(self, mock_wrapper_class):
        """测试设置 Ollama embeddings"""
        mock_wrapper = MagicMock()
        mock_wrapper_class.return_value = mock_wrapper

        from langchain_llm_toolkit.rag import RAGSystem

        rag = RAGSystem(embedding_type="ollama", embedding_model="test-model")
        result = rag.setup_embeddings()

        self.assertEqual(result, mock_wrapper)
        self.assertEqual(rag.embeddings, mock_wrapper)
        mock_wrapper_class.assert_called_once()

    @patch("langchain_llm_toolkit.rag.OpenAIEmbeddings")
    def test_setup_embeddings_openai(self, mock_openai_class):
        """测试设置 OpenAI embeddings"""
        mock_embeddings = MagicMock()
        mock_openai_class.return_value = mock_embeddings

        from langchain_llm_toolkit.rag import RAGSystem

        rag = RAGSystem(embedding_type="openai")
        result = rag.setup_embeddings()

        self.assertEqual(result, mock_embeddings)
        self.assertEqual(rag.embeddings, mock_embeddings)


class TestRAGSystemRerank(unittest.TestCase):
    """测试 RAGSystem 重排序功能"""

    def setUp(self):
        from langchain_llm_toolkit.rag import RAGSystem
        from langchain_core.documents import Document

        self.rag = RAGSystem()
        self.docs = [
            Document(
                page_content="Python is a programming language", metadata={"source": "doc1.txt"}
            ),
            Document(
                page_content="Java is also a programming language", metadata={"source": "doc2.txt"}
            ),
            Document(
                page_content="JavaScript is used for web development",
                metadata={"source": "doc3.txt"},
            ),
        ]

    @patch("langchain_llm_toolkit.rag.LLMIntegration")
    def test_rerank_documents_success(self, mock_llm_class):
        """测试成功重排序文档"""
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "2,1,3"
        mock_llm_class.return_value = mock_llm

        self.rag.llm_integration = mock_llm

        result = self.rag.rerank_documents("programming language", self.docs, top_k=2)

        self.assertEqual(len(result), 2)
        mock_llm.generate.assert_called_once()

    @patch("langchain_llm_toolkit.rag.LLMIntegration")
    def test_rerank_documents_with_error(self, mock_llm_class):
        """测试重排序出错时返回原始文档"""
        mock_llm = MagicMock()
        mock_llm.generate.side_effect = Exception("API Error")
        mock_llm_class.return_value = mock_llm

        self.rag.llm_integration = mock_llm

        result = self.rag.rerank_documents("programming language", self.docs, top_k=2)

        self.assertEqual(len(result), 2)


class TestRAGSystemGenerateSummary(unittest.TestCase):
    """测试 RAGSystem 摘要生成"""

    @patch("langchain_llm_toolkit.rag.LLMIntegration")
    def test_generate_summary(self, mock_llm_class):
        """测试生成摘要"""
        from langchain_llm_toolkit.rag import RAGSystem
        from langchain_core.documents import Document

        mock_llm = MagicMock()
        mock_llm.generate.return_value = "This is a summary"
        mock_llm_class.return_value = mock_llm

        rag = RAGSystem()
        rag.llm_integration = mock_llm

        docs = [Document(page_content="Long content here", metadata={"source": "test.txt"})]
        result = rag.generate_summary(docs)

        self.assertEqual(result, "This is a summary")
        mock_llm.generate.assert_called_once()


class TestRAGSystemExtractInformation(unittest.TestCase):
    """测试 RAGSystem 信息提取"""

    @patch("langchain_llm_toolkit.rag.LLMIntegration")
    def test_extract_information(self, mock_llm_class):
        """测试信息提取"""
        from langchain_llm_toolkit.rag import RAGSystem
        from langchain_core.documents import Document

        mock_llm = MagicMock()
        mock_llm.generate.return_value = "Extracted: key information"
        mock_llm_class.return_value = mock_llm

        rag = RAGSystem()
        rag.llm_integration = mock_llm

        docs = [
            Document(page_content="Document with key information", metadata={"source": "test.txt"})
        ]
        result = rag.extract_information(docs, "key information")

        self.assertEqual(result, "Extracted: key information")
        mock_llm.generate.assert_called_once()


if __name__ == "__main__":
    unittest.main()
