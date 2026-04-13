from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime


class GenerateRequest(BaseModel):
    """文本生成请求"""

    prompt: str = Field(..., description="输入提示", min_length=1, max_length=10000)
    model: str = Field(default="ollama/gemma3", description="模型名称")
    temperature: float = Field(default=0.7, description="温度参数", ge=0, le=2)
    timeout: int = Field(default=30, description="超时时间（秒）", gt=0)

    @field_validator("prompt")
    @classmethod
    def validate_prompt(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Prompt cannot be empty")
        return v.strip()


class GenerateResponse(BaseModel):
    """文本生成响应"""

    response: str = Field(..., description="生成的文本")
    model: str = Field(..., description="使用的模型")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")
    elapsed_time: Optional[float] = Field(None, description="耗时（秒）")


class ChatMessage(BaseModel):
    """聊天消息"""

    role: str = Field(..., description="角色 (system/user/assistant)")
    content: str = Field(..., description="消息内容", min_length=1)

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v not in ["system", "user", "assistant"]:
            raise ValueError("Role must be one of: system, user, assistant")
        return v


class ChatRequest(BaseModel):
    """聊天请求"""

    messages: List[ChatMessage] = Field(..., description="消息列表", min_length=1)
    model: str = Field(default="ollama/gemma3", description="模型名称")
    temperature: float = Field(default=0.7, description="温度参数", ge=0, le=2)
    timeout: int = Field(default=30, description="超时时间（秒）", gt=0)


class ChatResponse(BaseModel):
    """聊天响应"""

    response: str = Field(..., description="生成的回复")
    model: str = Field(..., description="使用的模型")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")
    elapsed_time: Optional[float] = Field(None, description="耗时（秒）")


class RAGQueryRequest(BaseModel):
    """RAG 查询请求"""

    query: str = Field(..., description="查询内容", min_length=1)
    k: int = Field(default=3, description="返回的相关文档数量", gt=0, le=10)

    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Query cannot be empty")
        return v.strip()


class SourceDocument(BaseModel):
    """源文档"""

    content: str = Field(..., description="文档内容")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class RAGQueryResponse(BaseModel):
    """RAG 查询响应"""

    answer: str = Field(..., description="生成的回答")
    sources: List[SourceDocument] = Field(..., description="相关文档")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")


class RAGUploadResponse(BaseModel):
    """RAG 上传响应"""

    message: str = Field(..., description="处理结果")
    filename: str = Field(..., description="文件名")
    documents_count: int = Field(..., description="文档数量")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")


class ModelInfo(BaseModel):
    """模型信息"""

    name: str = Field(..., description="模型名称")
    type: str = Field(..., description="模型类型")
    description: str = Field(..., description="模型描述")


class ModelsResponse(BaseModel):
    """模型列表响应"""

    models: List[ModelInfo] = Field(..., description="模型列表")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")


class HealthResponse(BaseModel):
    """健康检查响应"""

    status: str = Field(..., description="服务状态")
    version: str = Field(..., description="API 版本")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")
