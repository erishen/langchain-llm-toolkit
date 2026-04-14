# Claude 集成指南

本指南介绍如何在 `langchain-llm-toolkit` 中使用 Claude 模型。

## 支持的 Claude 模型

- `claude-3-opus-20240229` - 最强大的 Claude 模型
- `claude-3-sonnet-20240229` - 平衡性能和速度
- `claude-3-haiku-20240307` - 快速且经济
- `claude-2.1` - 上一代模型
- `claude-2.0` - 上一代模型
- `claude-instant-1.2` - 快速响应模型

## 配置 API 密钥

### 环境变量方式

```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

### .env 文件方式

在项目根目录创建 `.env` 文件：

```
ANTHROPIC_API_KEY=your-api-key-here
```

## 基本使用

### 直接生成

```python
from langchain_llm_toolkit import LLMIntegration

# 初始化 LLM
llm = LLMIntegration()
llm.set_model("claude-3-sonnet-20240229")

# 生成文本
response = llm.generate("Explain quantum computing in simple terms")
print(response)
```

### 聊天模式

```python
from langchain_llm_toolkit import LLMIntegration

llm = LLMIntegration()
llm.set_model("claude-3-sonnet-20240229")

messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is the capital of France?"},
]

response = llm.chat(messages)
print(response)
```

## 与 Agent 结合使用

```python
from langchain_llm_toolkit import LLMIntegration
from langchain_llm_toolkit.agent import ReActAgent, CalculatorTool

# 配置 Claude
llm = LLMIntegration()
llm.set_model("claude-3-opus-20240229")
llm.set_temperature(0.7)

# 创建 Agent
agent = ReActAgent(
    llm=llm,
    name="ClaudeAgent",
    max_iterations=10,
)

# 注册工具
agent.register_tool("calculator", CalculatorTool())

# 运行任务
response = agent.run(
    "Calculate the area of a circle with radius 5, then multiply by 3"
)
print(response.content)
```

## 高级配置

### 调整参数

```python
from langchain_llm_toolkit import LLMIntegration

llm = LLMIntegration(
    timeout=60,           # 超时时间（秒）
    max_retries=3,        # 最大重试次数
    enable_cache=True,    # 启用缓存
    cache_ttl=3600,       # 缓存过期时间（秒）
)

llm.set_model("claude-3-opus-20240229")
llm.set_temperature(0.5)  # 创造性程度 (0-2)
```

### 流式输出

```python
from langchain_llm_toolkit import LLMIntegration

llm = LLMIntegration()
llm.set_model("claude-3-sonnet-20240229")

# 注意：Claude 通过 LiteLLM 支持流式输出
for chunk in llm.generate_stream("Write a short poem about AI"):
    print(chunk, end="", flush=True)
```

## 模型选择建议

| 场景 | 推荐模型 | 原因 |
|------|---------|------|
| 复杂推理 | claude-3-opus | 最强的推理能力 |
| 日常对话 | claude-3-sonnet | 平衡性能和质量 |
| 快速响应 | claude-3-haiku | 最快的响应速度 |
| 代码生成 | claude-3-opus | 优秀的代码理解 |
| 长文档处理 | claude-3-opus | 200K 上下文窗口 |

## 成本优化

### 使用缓存

```python
from langchain_llm_toolkit import LLMIntegration

llm = LLMIntegration(
    enable_cache=True,
    cache_ttl=7200,  # 2小时缓存
)
```

### 选择合适的模型

```python
# 简单任务使用 haiku
llm.set_model("claude-3-haiku-20240307")

# 复杂任务使用 opus
llm.set_model("claude-3-opus-20240229")
```

### 速率限制

```python
from langchain_llm_toolkit import LLMIntegration

llm = LLMIntegration(
    rate_limit_requests=50,   # 每分钟请求数
    rate_limit_window=60,     # 时间窗口（秒）
)
```

## 错误处理

```python
from langchain_llm_toolkit import LLMIntegration
from langchain_llm_toolkit.exceptions import (
    APIKeyMissingError,
    APIConnectionError,
    RateLimitExceededError,
)

llm = LLMIntegration()
llm.set_model("claude-3-sonnet-20240229")

try:
    response = llm.generate("Hello")
except APIKeyMissingError:
    print("请设置 ANTHROPIC_API_KEY 环境变量")
except APIConnectionError:
    print("网络连接失败，请检查网络")
except RateLimitExceededError:
    print("超出速率限制，请稍后再试")
```

## 与 RAG 结合

```python
from langchain_llm_toolkit import LLMIntegration, RAGSystem

# 配置 Claude
llm = LLMIntegration()
llm.set_model("claude-3-opus-20240229")

# 创建 RAG 系统
rag = RAGSystem(
    embedding_type="openai",  # 或 "ollama"
)

# 添加文档
rag.add_documents_from_text("Your document content here...")

# 查询
query = "What are the main points?"
results = rag.query(query, k=3)

# 使用 Claude 生成回答
context = "\n".join([doc.page_content for doc in results])
prompt = f"Based on the following context, answer the question:\n\nContext: {context}\n\nQuestion: {query}"

response = llm.generate(prompt)
print(response)
```

## 最佳实践

1. **API 密钥安全**
   - 使用环境变量存储 API 密钥
   - 不要将密钥提交到版本控制
   - 定期轮换密钥

2. **错误处理**
   - 始终包装 API 调用在 try-except 中
   - 实现重试机制
   - 记录错误日志

3. **成本控制**
   - 启用缓存减少重复请求
   - 根据任务选择合适的模型
   - 监控使用量

4. **性能优化**
   - 使用流式输出提高响应速度
   - 设置合理的超时时间
   - 实现速率限制

## 故障排除

### API 密钥错误

```
APIKeyMissingError: ANTHROPIC_API_KEY not found
```

**解决方案**：
```bash
export ANTHROPIC_API_KEY="your-key"
```

### 速率限制

```
RateLimitExceededError: Rate limit exceeded
```

**解决方案**：
- 降低请求频率
- 增加 `rate_limit_requests` 值
- 联系 Anthropic 提高限制

### 连接超时

```
APITimeoutError: Request timed out
```

**解决方案**：
```python
llm = LLMIntegration(timeout=120)  # 增加超时时间
```

## 参考

- [Anthropic 官方文档](https://docs.anthropic.com/)
- [LiteLLM Claude 文档](https://docs.litellm.ai/docs/providers/anthropic)
- [langchain-llm-toolkit Agent 文档](./Agent.md)
