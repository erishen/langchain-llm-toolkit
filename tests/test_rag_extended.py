"""
Tests for RAG System - Extended Coverage.
RAG 系统扩展测试
"""

import os
import tempfile
from datetime import timedelta
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from langchain_llm_toolkit.rag import (
    OllamaEmbeddingsWrapper,
    QueryCache,
    RAGSystem,
)


class MockEmbeddings(Embeddings):
    """Mock embeddings for testing"""

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [np.random.rand(1536).tolist() for _ in texts]

    def embed_query(self, text: str) -> list[float]:
        return np.random.rand(1536).tolist()


class TestQueryCache:
    """测试查询缓存"""

    def test_init(self):
        """测试初始化"""
        cache = QueryCache(max_size=10, ttl_seconds=60)
        assert cache._max_size == 10
        assert cache._ttl == timedelta(seconds=60)

    def test_hash_query(self):
        """测试查询哈希"""
        cache = QueryCache()
        hash1 = cache._hash_query("test query", 5)
        hash2 = cache._hash_query("test query", 5)
        hash3 = cache._hash_query("test query", 10)

        assert hash1 == hash2
        assert hash1 != hash3
        assert len(hash1) == 32

    def test_set_and_get(self):
        """测试设置和获取缓存"""
        cache = QueryCache()
        docs = [Document(page_content="test", metadata={})]

        cache.set("test query", 5, docs)
        result = cache.get("test query", 5)

        assert result is not None
        assert len(result) == 1
        assert result[0].page_content == "test"

    def test_get_not_found(self):
        """测试获取不存在的缓存"""
        cache = QueryCache()
        result = cache.get("nonexistent", 5)
        assert result is None

    def test_cache_expiry(self):
        """测试缓存过期"""
        cache = QueryCache(ttl_seconds=0)

        docs = [Document(page_content="test", metadata={})]
        cache.set("test query", 5, docs)

        import time

        time.sleep(0.1)
        result = cache.get("test query", 5)
        assert result is None

    def test_cache_max_size(self):
        """测试缓存最大大小"""
        cache = QueryCache(max_size=2)

        for i in range(5):
            docs = [Document(page_content=f"doc{i}", metadata={})]
            cache.set(f"query{i}", 5, docs)

        assert len(cache._cache) <= 2

    def test_clear(self):
        """测试清空缓存"""
        cache = QueryCache()
        docs = [Document(page_content="test", metadata={})]

        cache.set("query1", 5, docs)
        cache.set("query2", 5, docs)

        cache.clear()
        assert len(cache._cache) == 0


class TestOllamaEmbeddingsWrapper:
    """测试 Ollama Embeddings 包装器"""

    @pytest.mark.skip(reason="需要 ollama 模块安装")
    def test_init_default(self):
        """测试默认初始化"""
        pass

    @pytest.mark.skip(reason="需要 ollama 模块安装")
    def test_init_custom(self):
        """测试自定义初始化"""
        pass

    @pytest.mark.skip(reason="需要 ollama 模块安装")
    def test_embed_query(self):
        """测试嵌入查询"""
        pass

    @pytest.mark.skip(reason="需要 ollama 模块安装")
    def test_embed_documents(self):
        """测试嵌入多个文档"""
        pass

    @pytest.mark.skip(reason="需要 ollama 模块安装")
    def test_embed_query_with_num_ctx(self):
        """测试带 num_ctx 的嵌入查询"""
        pass

    def test_models_need_num_ctx(self):
        """测试需要 num_ctx 的模型"""
        assert "nomic-embed-text" in OllamaEmbeddingsWrapper.MODELS_NEED_NUM_CTX


class TestRAGSystemInit:
    """测试 RAG 系统初始化"""

    def test_init_default(self):
        """测试默认初始化"""
        rag = RAGSystem()
        assert rag.vector_store_type == "qdrant"
        assert rag.embedding_type == "ollama"
        assert rag.embedding_model == "snowflake-arctic-embed2"
        assert rag.llm_model == "ollama/gemma4"

    def test_init_custom(self):
        """测试自定义初始化"""
        rag = RAGSystem(
            vector_store_type="faiss",
            embedding_type="openai",
            embedding_model="text-embedding-3-small",
            llm_model="gpt-4o",
            collection_name="test_collection",
        )
        assert rag.vector_store_type == "faiss"
        assert rag.embedding_type == "openai"
        assert rag.llm_model == "gpt-4o"
        assert rag.qdrant_collection_name == "test_collection"

    def test_init_with_env_vars(self):
        """测试使用环境变量初始化"""
        with patch.dict(
            os.environ,
            {
                "RAG_COLLECTION_NAME": "env_collection",
                "RAG_QDRANT_PATH": "/tmp/qdrant",
                "RAG_FAISS_PATH": "/tmp/faiss",
            },
        ):
            rag = RAGSystem()
            assert rag.qdrant_collection_name == "env_collection"
            assert rag.qdrant_persist_dir == "/tmp/qdrant"
            assert rag.faiss_persist_dir == "/tmp/faiss"

    def test_query_cache_created(self):
        """测试查询缓存创建"""
        rag = RAGSystem()
        assert rag.query_cache is not None
        assert isinstance(rag.query_cache, QueryCache)


class TestRAGSystemSetup:
    """测试 RAG 系统设置"""

    @pytest.mark.skip(reason="需要 ollama 模块安装")
    def test_setup_embeddings_ollama(self):
        """测试设置 Ollama 嵌入"""
        pass

    def test_setup_embeddings_openai(self):
        """测试设置 OpenAI 嵌入"""
        with patch("langchain_llm_toolkit.rag.OpenAIEmbeddings") as mock_openai:
            mock_openai.return_value = MagicMock()

            rag = RAGSystem(embedding_type="openai")
            embeddings = rag.setup_embeddings()

            assert embeddings is not None
            mock_openai.assert_called_once()


class TestRAGSystemVectorStore:
    """测试 RAG 系统向量存储"""

    def test_create_vector_store_faiss(self):
        """测试创建 FAISS 向量存储"""
        with tempfile.TemporaryDirectory() as temp_dir:
            rag = RAGSystem(
                vector_store_type="faiss",
                faiss_persist_dir=temp_dir,
            )
            rag.embeddings = MockEmbeddings()

            documents = [
                Document(page_content="Test document 1", metadata={"source": "test"}),
                Document(page_content="Test document 2", metadata={"source": "test"}),
            ]

            with patch.object(
                rag.text_splitter, "split_documents", return_value=documents
            ), patch("langchain_llm_toolkit.rag.FAISS") as mock_faiss:
                mock_faiss.from_documents.return_value = MagicMock()

                vector_store = rag.create_vector_store(documents)
                assert vector_store is not None


class TestRAGSystemMethods:
    """测试 RAG 系统方法"""

    def test_add_documents(self):
        """测试添加文档"""
        with tempfile.TemporaryDirectory() as temp_dir:
            rag = RAGSystem(
                vector_store_type="faiss",
                faiss_persist_dir=temp_dir,
            )
            rag.embeddings = MockEmbeddings()
            rag.vector_store = MagicMock()

            documents = [Document(page_content="Test", metadata={})]

            with patch.object(
                rag.text_splitter, "split_documents", return_value=documents
            ):
                rag.add_documents(documents)
                rag.vector_store.add_documents.assert_called_once()

    def test_query_cache(self):
        """测试查询缓存"""
        rag = RAGSystem()
        assert rag.query_cache is not None

        docs = [Document(page_content="test", metadata={})]
        rag.query_cache.set("query", 5, docs)
        result = rag.query_cache.get("query", 5)
        assert result is not None

    def test_prompt_builder(self):
        """测试提示构建器"""
        rag = RAGSystem()
        assert rag.prompt_builder is not None
