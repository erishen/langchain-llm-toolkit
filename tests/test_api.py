from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient
from langchain_llm_toolkit.api import app


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

    @patch("langchain_llm_toolkit.api.LLMIntegration")
    def test_generate_text_success(self, mock_llm_class, client):
        """测试文本生成成功"""
        mock_llm = Mock()
        mock_llm.generate.return_value = "这是一个测试响应"
        mock_llm_class.return_value = mock_llm

        response = client.post(
            "/api/v1/generate",
            json={
                "prompt": "你好",
                "model": "ollama/gemma3",
                "temperature": 0.7,
                "timeout": 30,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert data["model"] == "ollama/gemma3"
        assert "elapsed_time" in data

        mock_llm.set_model.assert_called_once_with("ollama/gemma3")
        mock_llm.set_temperature.assert_called_once_with(0.7)
        mock_llm.generate.assert_called_once_with("你好")

    @patch("langchain_llm_toolkit.api.LLMIntegration")
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

    @patch("langchain_llm_toolkit.api.LLMIntegration")
    def test_generate_text_validation_error(self, mock_llm_class, client):
        """测试验证错误"""
        mock_llm = Mock()
        mock_llm.generate.side_effect = ValueError("Invalid input")
        mock_llm_class.return_value = mock_llm

        response = client.post("/api/v1/generate", json={"prompt": "测试"})

        assert response.status_code == 400
        assert "Invalid input" in response.json()["detail"]

    @patch("langchain_llm_toolkit.api.LLMIntegration")
    def test_generate_text_internal_error(self, mock_llm_class, client):
        """测试内部错误"""
        mock_llm = Mock()
        mock_llm.generate.side_effect = Exception("Internal error")
        mock_llm_class.return_value = mock_llm

        response = client.post("/api/v1/generate", json={"prompt": "测试"})

        assert response.status_code == 500
        assert "Internal error" in response.json()["detail"]

    @patch("langchain_llm_toolkit.api.LLMIntegration")
    def test_generate_stream_success(self, mock_llm_class, client):
        """测试流式生成成功"""
        mock_llm = Mock()
        mock_llm.generate_stream.return_value = iter(["chunk1", "chunk2", "chunk3"])
        mock_llm_class.return_value = mock_llm

        response = client.post(
            "/api/v1/generate/stream",
            json={"prompt": "测试流式", "model": "ollama/gemma3"},
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

    @patch("langchain_llm_toolkit.api.LLMIntegration")
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

    @patch("langchain_llm_toolkit.api.LLMIntegration")
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

    @patch("langchain_llm_toolkit.api.LLMIntegration")
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

    @patch("langchain_llm_toolkit.api.get_rag_system")
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

    @patch("langchain_llm_toolkit.api.get_rag_system")
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

    @patch("langchain_llm_toolkit.api.get_rag_system")
    def test_rag_upload_success(self, mock_get_rag, client):
        """测试文档上传成功"""
        mock_rag = Mock()
        mock_rag.load_and_process_documents.return_value = ["doc1", "doc2"]
        mock_rag.create_vector_store.return_value = None
        mock_rag.save_vector_store.return_value = None
        mock_get_rag.return_value = mock_rag

        test_content = b"This is test content"

        response = client.post(
            "/api/v1/rag/upload",
            files={"file": ("test.txt", test_content, "text/plain")},
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

    @patch("langchain_llm_toolkit.api.get_rag_system")
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

    @patch("langchain_llm_toolkit.api.get_rag_system")
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

    @patch("langchain_llm_toolkit.api.get_rag_system")
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
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
            },
        )

        assert response.status_code == 200


class TestStreamingEndpoints:
    """测试流式响应端点"""

    @patch("langchain_llm_toolkit.api.LLMIntegration")
    def test_generate_stream_success(self, mock_llm_class, client):
        """测试流式生成成功"""
        mock_llm = Mock()
        mock_llm.generate_stream.return_value = iter(["Hello", " ", "World"])
        mock_llm_class.return_value = mock_llm

        response = client.post(
            "/api/v1/generate/stream",
            json={"prompt": "测试", "model": "ollama/gemma3"},
        )

        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]

    def test_generate_stream_non_ollama_model(self, client):
        """测试非 Ollama 模型的流式生成"""
        response = client.post(
            "/api/v1/generate/stream",
            json={"prompt": "测试", "model": "gpt-4o"},
        )

        assert response.status_code == 400
        assert "Streaming only supported for Ollama models" in response.json()["detail"]

    @patch("langchain_llm_toolkit.api.LLMIntegration")
    def test_chat_stream_success(self, mock_llm_class, client):
        """测试聊天流式响应"""
        mock_llm = Mock()
        mock_llm.chat_stream.return_value = iter(["你好", "！"])
        mock_llm_class.return_value = mock_llm

        response = client.post(
            "/api/v1/chat/stream",
            json={
                "messages": [{"role": "user", "content": "你好"}],
                "model": "ollama/gemma3",
            },
        )

        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]

    def test_chat_stream_non_ollama_model(self, client):
        """测试非 Ollama 模型的聊天流式"""
        response = client.post(
            "/api/v1/chat/stream",
            json={
                "messages": [{"role": "user", "content": "你好"}],
                "model": "gpt-4o",
            },
        )

        assert response.status_code == 400


class TestHybridRAGEndpoints:
    """测试混合 RAG 端点"""

    @patch("langchain_llm_toolkit.api.get_hybrid_rag")
    def test_hybrid_rag_query_success(self, mock_get_hybrid_rag, client):
        """测试混合 RAG 查询"""
        from langchain_core.documents import Document

        mock_hybrid = Mock()
        mock_hybrid.rag = Mock()
        mock_hybrid.rag.load_vector_store.return_value = None
        mock_hybrid.generate_answer.return_value = (
            "这是混合检索的答案",
            [Document(page_content="文档内容", metadata={"source": "test.txt"})],
        )
        mock_get_hybrid_rag.return_value = mock_hybrid

        response = client.post(
            "/api/v1/rag/hybrid?alpha=0.3",
            json={"query": "测试查询", "k": 3},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["answer"] == "这是混合检索的答案"


class TestConversationEndpoints:
    """测试对话管理端点"""

    @patch("langchain_llm_toolkit.api.get_conversation_store")
    def test_create_conversation(self, mock_get_store, client):
        """测试创建对话"""
        mock_store = Mock()
        mock_store.save_conversation.return_value = True
        mock_get_store.return_value = mock_store

        response = client.post("/api/v1/conversations?title=新对话")

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["title"] == "新对话"

    @patch("langchain_llm_toolkit.api.get_conversation_store")
    def test_list_conversations(self, mock_get_store, client):
        """测试列出对话"""
        from langchain_llm_toolkit.conversation_store import Conversation

        mock_store = Mock()
        mock_store.list_conversations.return_value = [
            Conversation(
                id="conv-1",
                title="对话1",
                messages=[],
                created_at="2024-01-01T00:00:00",
                updated_at="2024-01-01T00:00:00",
            ),
        ]
        mock_get_store.return_value = mock_store

        response = client.get("/api/v1/conversations")

        assert response.status_code == 200
        data = response.json()
        assert len(data["conversations"]) == 1

    @patch("langchain_llm_toolkit.api.get_conversation_store")
    def test_get_conversation(self, mock_get_store, client):
        """测试获取对话"""
        from langchain_llm_toolkit.conversation_store import Conversation

        mock_store = Mock()
        mock_store.get_conversation.return_value = Conversation(
            id="conv-1",
            title="测试对话",
            messages=[],
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
        )
        mock_get_store.return_value = mock_store

        response = client.get("/api/v1/conversations/conv-1")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "conv-1"

    @patch("langchain_llm_toolkit.api.get_conversation_store")
    def test_get_conversation_not_found(self, mock_get_store, client):
        """测试获取不存在的对话"""
        mock_store = Mock()
        mock_store.get_conversation.return_value = None
        mock_get_store.return_value = mock_store

        response = client.get("/api/v1/conversations/nonexistent")

        assert response.status_code == 404

    @patch("langchain_llm_toolkit.api.get_conversation_store")
    def test_delete_conversation(self, mock_get_store, client):
        """测试删除对话"""
        mock_store = Mock()
        mock_store.delete_conversation.return_value = True
        mock_get_store.return_value = mock_store

        response = client.delete("/api/v1/conversations/conv-1")

        assert response.status_code == 200
        assert response.json()["message"] == "Conversation deleted"

    def test_conversation_stats(self, client):
        """测试对话统计"""
        response = client.get("/api/v1/conversations/stats")

        assert response.status_code == 200
        data = response.json()
        assert "total_conversations" in data
        assert "total_messages" in data


class TestAuthEndpoints:
    """测试认证端点"""

    @patch("langchain_llm_toolkit.api.get_auth_manager")
    def test_register_success(self, mock_get_auth, client):
        """测试注册成功"""
        from langchain_llm_toolkit.auth import User

        mock_auth = Mock()
        mock_auth.create_user.return_value = User(
            id="user-1",
            username="testuser",
            email="test@example.com",
            hashed_password="hashed",
            created_at="2024-01-01T00:00:00",
        )
        mock_get_auth.return_value = mock_auth

        response = client.post(
            "/api/v1/auth/register?username=testuser&email=test@example.com&password=password123"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"

    @patch("langchain_llm_toolkit.api.get_auth_manager")
    def test_register_duplicate(self, mock_get_auth, client):
        """测试注册重复用户"""
        mock_auth = Mock()
        mock_auth.create_user.side_effect = ValueError("用户名已存在")
        mock_get_auth.return_value = mock_auth

        response = client.post(
            "/api/v1/auth/register?username=testuser&email=test@example.com&password=password123"
        )

        assert response.status_code == 400

    @patch("langchain_llm_toolkit.api.get_auth_manager")
    def test_login_success(self, mock_get_auth, client):
        """测试登录成功"""
        from langchain_llm_toolkit.auth import User

        mock_auth = Mock()
        mock_auth.authenticate_user.return_value = User(
            id="user-1",
            username="testuser",
            email="test@example.com",
            hashed_password="hashed",
            created_at="2024-01-01T00:00:00",
        )
        mock_auth.create_access_token.return_value = "test_token"
        mock_get_auth.return_value = mock_auth

        response = client.post("/api/v1/auth/login?username=testuser&password=password123")

        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "test_token"
        assert data["token_type"] == "bearer"

    @patch("langchain_llm_toolkit.api.get_auth_manager")
    def test_login_invalid_credentials(self, mock_get_auth, client):
        """测试登录失败"""
        mock_auth = Mock()
        mock_auth.authenticate_user.return_value = None
        mock_get_auth.return_value = mock_auth

        response = client.post("/api/v1/auth/login?username=testuser&password=wrongpassword")

        assert response.status_code == 401

    @patch("langchain_llm_toolkit.api.get_auth_manager")
    def test_create_api_key(self, mock_get_auth, client):
        """测试创建 API Key"""
        from langchain_llm_toolkit.auth import TokenData

        mock_auth = Mock()
        mock_auth.create_api_key.return_value = "lk-test_api_key"
        mock_get_auth.return_value = mock_auth

        def override_get_current_user():
            return TokenData(user_id="user-1", username="testuser", scopes=[])

        from langchain_llm_toolkit import api

        app.dependency_overrides[api.get_current_user] = override_get_current_user

        try:
            response = client.post("/api/v1/auth/api-keys?name=Test Key")
            assert response.status_code == 200
            data = response.json()
            assert data["api_key"] == "lk-test_api_key"
        finally:
            app.dependency_overrides.clear()

    @patch("langchain_llm_toolkit.api.get_auth_manager")
    def test_list_api_keys(self, mock_get_auth, client):
        """测试列出 API Keys"""
        from langchain_llm_toolkit.auth import TokenData

        mock_auth = Mock()
        mock_auth.store.list_api_keys.return_value = [
            {"key_id": "key-1", "name": "Key 1"},
        ]
        mock_get_auth.return_value = mock_auth

        def override_get_current_user():
            return TokenData(user_id="user-1", username="testuser", scopes=[])

        from langchain_llm_toolkit import api

        app.dependency_overrides[api.get_current_user] = override_get_current_user

        try:
            response = client.get("/api/v1/auth/api-keys")
            assert response.status_code == 200
            data = response.json()
            assert len(data["api_keys"]) == 1
        finally:
            app.dependency_overrides.clear()
