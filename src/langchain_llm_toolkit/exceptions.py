"""自定义异常类"""
from typing import Optional, Any


class LLMToolkitError(Exception):
    """LLM Toolkit 基础异常类"""

    def __init__(self, message: str, details: Optional[str] = None):
        self.message = message
        self.details = details
        super().__init__(self.message)

    def __str__(self):
        if self.details:
            return f"{self.message}\n详情: {self.details}"
        return self.message


class ModelNotFoundError(LLMToolkitError):
    """模型未找到异常"""

    def __init__(self, model: str, available_models: Optional[list] = None):
        message = f"模型 '{model}' 未找到或不支持"
        details = None
        if available_models:
            details = f"可用模型: {', '.join(available_models)}"
        super().__init__(message, details)


class APIKeyMissingError(LLMToolkitError):
    """API 密钥缺失异常"""

    def __init__(self, provider: str = "OpenAI"):
        message = f"{provider} API 密钥未设置"
        details = f"请设置 {provider.upper()}_API_KEY 环境变量"
        super().__init__(message, details)


class APIConnectionError(LLMToolkitError):
    """API 连接异常"""

    def __init__(self, provider: str, original_error: Optional[str] = None):
        message = f"无法连接到 {provider} API"
        details = original_error
        super().__init__(message, details)


class APITimeoutError(LLMToolkitError):
    """API 超时异常"""

    def __init__(self, provider: str, timeout: Optional[int] = None):
        message = f"{provider} API 请求超时"
        details = f"超时时间: {timeout}秒" if timeout else None
        super().__init__(message, details)


class RateLimitExceededError(LLMToolkitError):
    """速率限制超出异常"""

    def __init__(self, provider: str, retry_after: Optional[int] = None):
        message = f"{provider} API 速率限制已超出"
        details = f"请在 {retry_after} 秒后重试" if retry_after else "请稍后重试"
        super().__init__(message, details)


class DocumentProcessingError(LLMToolkitError):
    """文档处理异常"""

    def __init__(self, file_path: str, reason: Optional[str] = None):
        message = f"文档处理失败: {file_path}"
        details = reason
        super().__init__(message, details)


class VectorStoreError(LLMToolkitError):
    """向量存储异常"""

    def __init__(self, operation: str, reason: Optional[str] = None):
        message = f"向量存储操作失败: {operation}"
        details = reason
        super().__init__(message, details)


class EmbeddingError(LLMToolkitError):
    """Embedding 生成异常"""

    def __init__(self, text_length: Optional[int] = None, reason: Optional[str] = None):
        message = "Embedding 生成失败"
        details = reason
        if text_length:
            details = f"文本长度: {text_length}. {reason}" if reason else f"文本长度: {text_length}"
        super().__init__(message, details)


class ConfigurationError(LLMToolkitError):
    """配置异常"""

    def __init__(self, config_key: str, reason: Optional[str] = None):
        message = f"配置错误: {config_key}"
        details = reason
        super().__init__(message, details)


class ValidationError(LLMToolkitError):
    """验证异常"""

    def __init__(self, field: str, value: Any, reason: Optional[str] = None):
        message = f"验证失败: {field}={value}"
        details = reason
        super().__init__(message, details)


class CacheError(LLMToolkitError):
    """缓存异常"""

    def __init__(self, operation: str, reason: Optional[str] = None):
        message = f"缓存操作失败: {operation}"
        details = reason
        super().__init__(message, details)
