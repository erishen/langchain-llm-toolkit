import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from api import app


@pytest.fixture
def client():
    """创建测试客户端"""
    return TestClient(app)


class TestHealthEndpoints:
    """测试健康检查端点"""

    def test_root(self, client):
        """测试根路径"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"

    def test_health_check(self, client):
        """测试健康检查端点"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"


class TestGenerateEndpoints:
    """测试文本生成端点"""

    @patch("api.LLMIntegration")
    def test_generate_text_success(self, mock_llm_class, client):
        """测试文本生成成功"""
        mock_llm = Mock()
        mock_llm.generate.return_value = "这是一个测试响应"
        mock_llm_class.return_value = mock_llm

        response = client.post(
            "/api/v1/generate",
            json={"prompt": "你好", "model": "ollama/gemma3", "temperature": 0.7, "timeout": 30},
        )

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert data["model"] == "ollama/gemma3"
        assert "elapsed_time" in data

        mock_llm.set_model.assert_called_once_with("ollama/gemma3")
        mock_llm.set_temperature.assert_called_once_with(0.7)
        mock_llm.generate.assert_called_once_with("你好")

    @patch("api.LLMIntegration")
    def test_generate_text_with_default_params(self, mock_llm_class, client):
        """测试使用默认参数的文本生成"""
        mock_llm = Mock()
        mock_llm.generate.return_value = "默认参数响应"
        mock_llm_class.return_value = mock_llm

        response = client.post("/api/v1/generate", json={"prompt": "测试"})

        assert response.status_code == 200
        data = response.json()
        assert data["response"] == "默认参数响应"
        assert data["model"] == "ollama/gemma3"

    def test_generate_text_empty_prompt(self, client):
        """测试空提示词"""
        response = client.post("/api/v1/generate", json={"prompt": ""})
        assert response.status_code == 422

    def test_generate_text_missing_prompt(self, client):
        """测试缺少提示词"""
        response = client.post("/api/v1/generate", json={})
        assert response.status_code == 422

    @patch("api.LLMIntegration")
    def test_generate_text_validation_error(self, mock_llm_class, client):
        """测试验证错误"""
        mock_llm = Mock()
        mock_llm.generate.side_effect = ValueError("Invalid input")
        mock_llm_class.return_value = mock_llm

        response = client.post("/api/v1/generate", json={"prompt": "测试"})

        assert response.status_code == 400
        assert "Invalid input" in response.json()["detail"]

    @patch("api.LLMIntegration")
    def test_generate_text_internal_error(self, mock_llm_class, client):
        """测试内部错误"""
        mock_llm = Mock()
        mock_llm.generate.side_effect = Exception("Internal error")
        mock_llm_class.return_value = mock_llm

        response = client.post("/api/v1/generate", json={"prompt": "测试"})

        assert response.status_code == 500
        assert "Internal error" in response.json()["detail"]

    @patch("api.LLMIntegration")
    def test_generate_stream_success(self, mock_llm_class, client):
        """测试流式生成成功"""
        mock_llm = Mock()
        mock_llm.generate_stream.return_value = iter(["chunk1", "chunk2", "chunk3"])
        mock_llm_class.return_value = mock_llm

        response = client.post(
            "/api/v1/generate/stream", json={"prompt": "测试流式", "model": "ollama/gemma3"}
        )

        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]

    def test_generate_stream_non_ollama_model(self, client):
        """测试非 Ollama 模型的流式生成"""
        response = client.post(
            "/api/v1/generate/stream", json={"prompt": "测试", "model": "gpt-4o"}
        )

        assert response.status_code == 400
        assert "Streaming only supported for Ollama models" in response.json()["detail"]


class TestChatEndpoints:
    """测试聊天端点"""

    @patch("api.LLMIntegration")
    def test_chat_success(self, mock_llm_class, client):
        """测试聊天成功"""
        mock_llm = Mock()
        mock_llm.chat.return_value = "聊天响应"
        mock_llm_class.return_value = mock_llm

        response = client.post(
            "/api/v1/chat",
            json={
                "messages": [{"role": "user", "content": "你好"}],
                "model": "ollama/gemma3",
                "temperature": 0.7,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["response"] == "聊天响应"
        assert data["model"] == "ollama/gemma3"

        mock_llm.chat.assert_called_once_with([{"role": "user", "content": "你好"}])

    @patch("api.LLMIntegration")
    def test_chat_with_multiple_messages(self, mock_llm_class, client):
        """测试多轮聊天"""
        mock_llm = Mock()
        mock_llm.chat.return_value = "多轮对话响应"
        mock_llm_class.return_value = mock_llm

        response = client.post(
            "/api/v1/chat",
            json={
                "messages": [
                    {"role": "user", "content": "你好"},
                    {"role": "assistant", "content": "你好！有什么可以帮助你的吗？"},
                    {"role": "user", "content": "介绍一下自己"},
                ]
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["response"] == "多轮对话响应"

    def test_chat_empty_messages(self, client):
        """测试空消息列表"""
        response = client.post("/api/v1/chat", json={"messages": []})
        assert response.status_code == 422

    def test_chat_missing_messages(self, client):
        """测试缺少消息"""
        response = client.post("/api/v1/chat", json={})
        assert response.status_code == 422

    @patch("api.LLMIntegration")
    def test_chat_validation_error(self, mock_llm_class, client):
        """测试聊天验证错误"""
        mock_llm = Mock()
        mock_llm.chat.side_effect = ValueError("Invalid messages")
        mock_llm_class.return_value = mock_llm

        response = client.post(
            "/api/v1/chat", json={"messages": [{"role": "user", "content": "测试"}]}
        )

        assert response.status_code == 400


class TestRAGEndpoints:
    """测试 RAG 端点"""

    @patch("api.get_rag_system")
    def test_rag_query_success(self, mock_get_rag, client):
        """测试 RAG 查询成功"""
        from langchain_core.documents import Document

        mock_rag = Mock()
        mock_rag.load_vector_store.return_value = None
        mock_rag.generate_answer.return_value = (
            "这是答案",
            [
                Document(page_content="文档1", metadata={"source": "test1.txt"}),
                Document(page_content="文档2", metadata={"source": "test2.txt"}),
            ],
        )
        mock_get_rag.return_value = mock_rag

        response = client.post("/api/v1/rag/query", json={"query": "测试查询", "k": 2})

        assert response.status_code == 200
        data = response.json()
        assert data["answer"] == "这是答案"
        assert len(data["sources"]) == 2
        assert data["sources"][0]["content"] == "文档1"

    @patch("api.get_rag_system")
    def test_rag_query_vector_store_not_found(self, mock_get_rag, client):
        """测试向量存储不存在"""
        mock_rag = Mock()
        mock_rag.load_vector_store.side_effect = Exception("Vector store not found")
        mock_get_rag.return_value = mock_rag

        response = client.post("/api/v1/rag/query", json={"query": "测试查询"})

        assert response.status_code == 404
        assert "Vector store not found" in response.json()["detail"]

    def test_rag_query_missing_query(self, client):
        """测试缺少查询参数"""
        response = client.post("/api/v1/rag/query", json={})
        assert response.status_code == 422

    @patch("api.get_rag_system")
    def test_rag_upload_success(self, mock_get_rag, client):
        """测试文档上传成功"""
        mock_rag = Mock()
        mock_rag.load_and_process_documents.return_value = ["doc1", "doc2"]
        mock_rag.create_vector_store.return_value = None
        mock_rag.save_vector_store.return_value = None
        mock_get_rag.return_value = mock_rag

        test_content = b"This is test content"

        response = client.post(
            "/api/v1/rag/upload", files={"file": ("test.txt", test_content, "text/plain")}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "File processed successfully"
        assert data["filename"] == "test.txt"
        assert data["documents_count"] == 2

    def test_rag_upload_unsupported_file_type(self, client):
        """测试不支持的文件类型"""
        test_content = b"test content"

        response = client.post(
            "/api/v1/rag/upload",
            files={"file": ("test.xyz", test_content, "application/octet-stream")},
        )

        assert response.status_code == 400
        assert "File type not supported" in response.json()["detail"]

    def test_rag_upload_missing_file(self, client):
        """测试缺少文件"""
        response = client.post("/api/v1/rag/upload")
        assert response.status_code == 422

    @patch("api.get_rag_system")
    def test_rag_info_ready(self, mock_get_rag, client):
        """测试 RAG 系统信息 - 就绪状态"""
        mock_rag = Mock()
        mock_rag.vector_store_type = "faiss"
        mock_rag.get_collection_info.return_value = {"count": 10}
        mock_get_rag.return_value = mock_rag

        response = client.get("/api/v1/rag/info")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["vector_store_type"] == "faiss"
        assert "collection_info" in data

    @patch("api.get_rag_system")
    def test_rag_info_not_initialized(self, mock_get_rag, client):
        """测试 RAG 系统信息 - 未初始化"""
        mock_rag = Mock()
        mock_rag.vector_store_type = "faiss"
        mock_rag.get_collection_info.side_effect = Exception("Not initialized")
        mock_get_rag.return_value = mock_rag

        response = client.get("/api/v1/rag/info")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "not_initialized"
        assert "Vector store not initialized" in data["message"]

    @patch("api.get_rag_system")
    def test_rag_clear_success(self, mock_get_rag, client):
        """测试清空 RAG 向量存储"""
        mock_rag = Mock()
        mock_rag.delete_collection.return_value = None
        mock_get_rag.return_value = mock_rag

        response = client.delete("/api/v1/rag/clear")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Vector store cleared successfully"
        mock_rag.delete_collection.assert_called_once()


class TestModelsEndpoint:
    """测试模型列表端点"""

    def test_list_models(self, client):
        """测试获取模型列表"""
        response = client.get("/api/v1/models")

        assert response.status_code == 200
        data = response.json()
        assert "models" in data
        assert len(data["models"]) > 0

        model_names = [m["name"] for m in data["models"]]
        assert "ollama/gemma3" in model_names
        assert "gpt-4o" in model_names

        for model in data["models"]:
            assert "name" in model
            assert "type" in model
            assert "description" in model
            assert model["type"] in ["local", "cloud"]


class TestCORS:
    """测试 CORS 配置"""

    def test_cors_headers(self, client):
        """测试 CORS 头部"""
        response = client.options(
            "/api/v1/generate",
            headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "POST"},
        )

        assert response.status_code == 200
