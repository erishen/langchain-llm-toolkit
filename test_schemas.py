import pytest
from pydantic import ValidationError
from datetime import datetime

from models.schemas import (
    GenerateRequest,
    GenerateResponse,
    ChatMessage,
    ChatRequest,
    ChatResponse,
    RAGQueryRequest,
    RAGQueryResponse,
    RAGUploadResponse,
    SourceDocument,
    ModelInfo,
    ModelsResponse,
    HealthResponse,
)


class TestGenerateRequest:
    """测试文本生成请求模型"""

    def test_valid_request(self):
        """测试有效请求"""
        request = GenerateRequest(prompt="你好")
        assert request.prompt == "你好"
        assert request.model == "ollama/gemma3"
        assert request.temperature == 0.7
        assert request.timeout == 30

    def test_custom_parameters(self):
        """测试自定义参数"""
        request = GenerateRequest(prompt="测试", model="gpt-4o", temperature=1.2, timeout=60)
        assert request.prompt == "测试"
        assert request.model == "gpt-4o"
        assert request.temperature == 1.2
        assert request.timeout == 60

    def test_prompt_validation_empty(self):
        """测试空提示词验证"""
        with pytest.raises(ValidationError) as exc_info:
            GenerateRequest(prompt="")
        assert "at least 1 character" in str(exc_info.value)

    def test_prompt_validation_whitespace(self):
        """测试纯空白提示词验证"""
        with pytest.raises(ValidationError) as exc_info:
            GenerateRequest(prompt="   ")
        assert "Prompt cannot be empty" in str(exc_info.value)

    def test_prompt_stripped(self):
        """测试提示词去除空白"""
        request = GenerateRequest(prompt="  你好  ")
        assert request.prompt == "你好"

    def test_prompt_too_long(self):
        """测试提示词过长"""
        long_prompt = "a" * 10001
        with pytest.raises(ValidationError):
            GenerateRequest(prompt=long_prompt)

    def test_temperature_range_invalid_low(self):
        """测试温度参数过低"""
        with pytest.raises(ValidationError):
            GenerateRequest(prompt="测试", temperature=-0.1)

    def test_temperature_range_invalid_high(self):
        """测试温度参数过高"""
        with pytest.raises(ValidationError):
            GenerateRequest(prompt="测试", temperature=2.1)

    def test_timeout_invalid(self):
        """测试超时时间无效"""
        with pytest.raises(ValidationError):
            GenerateRequest(prompt="测试", timeout=0)

        with pytest.raises(ValidationError):
            GenerateRequest(prompt="测试", timeout=-1)


class TestGenerateResponse:
    """测试文本生成响应模型"""

    def test_valid_response(self):
        """测试有效响应"""
        response = GenerateResponse(response="这是生成的文本", model="ollama/gemma3")
        assert response.response == "这是生成的文本"
        assert response.model == "ollama/gemma3"
        assert isinstance(response.timestamp, datetime)

    def test_response_with_elapsed_time(self):
        """测试带耗时的响应"""
        response = GenerateResponse(response="测试", model="gpt-4o", elapsed_time=1.5)
        assert response.elapsed_time == 1.5


class TestChatMessage:
    """测试聊天消息模型"""

    def test_valid_user_message(self):
        """测试有效的用户消息"""
        message = ChatMessage(role="user", content="你好")
        assert message.role == "user"
        assert message.content == "你好"

    def test_valid_assistant_message(self):
        """测试有效的助手消息"""
        message = ChatMessage(role="assistant", content="你好！")
        assert message.role == "assistant"

    def test_valid_system_message(self):
        """测试有效的系统消息"""
        message = ChatMessage(role="system", content="你是一个助手")
        assert message.role == "system"

    def test_invalid_role(self):
        """测试无效角色"""
        with pytest.raises(ValidationError) as exc_info:
            ChatMessage(role="invalid", content="测试")
        assert "Role must be one of: system, user, assistant" in str(exc_info.value)

    def test_empty_content(self):
        """测试空内容"""
        with pytest.raises(ValidationError):
            ChatMessage(role="user", content="")


class TestChatRequest:
    """测试聊天请求模型"""

    def test_valid_request(self):
        """测试有效请求"""
        request = ChatRequest(messages=[ChatMessage(role="user", content="你好")])
        assert len(request.messages) == 1
        assert request.model == "ollama/gemma3"
        assert request.temperature == 0.7

    def test_multiple_messages(self):
        """测试多轮对话"""
        request = ChatRequest(
            messages=[
                ChatMessage(role="user", content="你好"),
                ChatMessage(role="assistant", content="你好！"),
                ChatMessage(role="user", content="介绍一下自己"),
            ]
        )
        assert len(request.messages) == 3

    def test_empty_messages(self):
        """测试空消息列表"""
        with pytest.raises(ValidationError):
            ChatRequest(messages=[])


class TestChatResponse:
    """测试聊天响应模型"""

    def test_valid_response(self):
        """测试有效响应"""
        response = ChatResponse(response="这是回复", model="ollama/gemma3")
        assert response.response == "这是回复"
        assert response.model == "ollama/gemma3"
        assert isinstance(response.timestamp, datetime)


class TestRAGQueryRequest:
    """测试 RAG 查询请求模型"""

    def test_valid_request(self):
        """测试有效请求"""
        request = RAGQueryRequest(query="测试查询")
        assert request.query == "测试查询"
        assert request.k == 3

    def test_custom_k(self):
        """测试自定义 k 值"""
        request = RAGQueryRequest(query="测试", k=5)
        assert request.k == 5

    def test_query_validation_empty(self):
        """测试空查询验证"""
        with pytest.raises(ValidationError) as exc_info:
            RAGQueryRequest(query="")
        assert "at least 1 character" in str(exc_info.value)

    def test_query_stripped(self):
        """测试查询去除空白"""
        request = RAGQueryRequest(query="  测试  ")
        assert request.query == "测试"

    def test_k_range_invalid_low(self):
        """测试 k 值过小"""
        with pytest.raises(ValidationError):
            RAGQueryRequest(query="测试", k=0)

    def test_k_range_invalid_high(self):
        """测试 k 值过大"""
        with pytest.raises(ValidationError):
            RAGQueryRequest(query="测试", k=11)


class TestSourceDocument:
    """测试源文档模型"""

    def test_valid_document(self):
        """测试有效文档"""
        doc = SourceDocument(content="文档内容", metadata={"source": "test.txt"})
        assert doc.content == "文档内容"
        assert doc.metadata == {"source": "test.txt"}

    def test_document_without_metadata(self):
        """测试无元数据的文档"""
        doc = SourceDocument(content="文档内容")
        assert doc.content == "文档内容"
        assert doc.metadata == {}


class TestRAGQueryResponse:
    """测试 RAG 查询响应模型"""

    def test_valid_response(self):
        """测试有效响应"""
        response = RAGQueryResponse(
            answer="这是答案",
            sources=[
                SourceDocument(content="文档1", metadata={"source": "test1.txt"}),
                SourceDocument(content="文档2", metadata={"source": "test2.txt"}),
            ],
        )
        assert response.answer == "这是答案"
        assert len(response.sources) == 2
        assert isinstance(response.timestamp, datetime)


class TestRAGUploadResponse:
    """测试 RAG 上传响应模型"""

    def test_valid_response(self):
        """测试有效响应"""
        response = RAGUploadResponse(message="处理成功", filename="test.pdf", documents_count=5)
        assert response.message == "处理成功"
        assert response.filename == "test.pdf"
        assert response.documents_count == 5
        assert isinstance(response.timestamp, datetime)


class TestModelInfo:
    """测试模型信息模型"""

    def test_valid_model_info(self):
        """测试有效模型信息"""
        info = ModelInfo(name="ollama/gemma3", type="local", description="Ollama gemma3 模型")
        assert info.name == "ollama/gemma3"
        assert info.type == "local"
        assert info.description == "Ollama gemma3 模型"


class TestModelsResponse:
    """测试模型列表响应模型"""

    def test_valid_response(self):
        """测试有效响应"""
        response = ModelsResponse(
            models=[
                ModelInfo(name="ollama/gemma3", type="local", description="本地模型"),
                ModelInfo(name="gpt-4o", type="cloud", description="云端模型"),
            ]
        )
        assert len(response.models) == 2
        assert isinstance(response.timestamp, datetime)


class TestHealthResponse:
    """测试健康检查响应模型"""

    def test_valid_response(self):
        """测试有效响应"""
        response = HealthResponse(status="healthy", version="1.0.0")
        assert response.status == "healthy"
        assert response.version == "1.0.0"
        assert isinstance(response.timestamp, datetime)
