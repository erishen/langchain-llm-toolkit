# LangChain LLM Toolkit

一个基于 LangChain 和 LiteLLM 的完整 LLM 工具集，支持文本生成、聊天对话和 RAG 文档问答功能。

## 功能特性

- **多模型集成**：使用 LiteLLM 调用各种 AI 模型（OpenAI、Anthropic、Google、Ollama 等）
- **文本生成**：支持基本文本生成和聊天模式，支持流式输出
- **RAG 系统**：实现检索增强生成，支持混合检索（BM25 + 语义检索）
- **文档处理**：支持加载和处理多种格式的文档（PDF、TXT、DOCX、Markdown）
- **向量存储**：支持 Qdrant 和 FAISS 向量数据库
- **对话持久化**：基于 SQLite 的对话历史存储
- **API 认证**：支持 JWT 和 API Key 认证
- **流式响应**：支持 SSE 流式 API 响应
- **性能优化**：LRU 缓存、查询缓存、并行处理

## 项目结构

```
langchain-llm-toolkit/
├── src/langchain_llm_toolkit/    # 源代码目录
│   ├── agent/                    # Agent 系统
│   ├── models/                   # 数据模型
│   ├── config/                   # 配置管理
│   ├── api.py                    # FastAPI 服务
│   ├── app.py                    # Streamlit Web UI
│   ├── rag.py                    # RAG 系统
│   ├── hybrid_retriever.py       # 混合检索器
│   ├── llm_integration.py        # LLM 集成
│   ├── conversation_store.py     # 对话持久化
│   ├── auth.py                   # 认证系统
│   ├── performance.py            # 性能优化
│   ├── cache.py                  # 缓存系统
│   └── ...
├── tests/                        # 测试用例
├── docs/                         # 文档
├── pyproject.toml                # 项目配置
├── Makefile                      # 构建命令
└── README.md                     # 项目文档
```

## 快速开始

### 安装

```bash
# 克隆项目
git clone <repository-url>
cd langchain-llm-toolkit

# 安装依赖（使用 uv）
make install

# 或使用 pip
pip install -e .
```

### 配置环境变量

创建 `.env` 文件：

```env
# API Keys（可选，使用 Ollama 本地模型时不需要）
OPENAI_API_KEY=your_openai_api_key

# Ollama 设置
OLLAMA_BASE_URL=http://localhost:11434

# 模型设置
DEFAULT_MODEL=ollama/gemma4
EMBEDDING_MODEL=snowflake-arctic-embed2
```

### 使用 Ollama 本地模型

```bash
# 安装 Ollama
brew install ollama  # macOS
# 或访问 https://ollama.com 下载

# 下载模型
ollama pull gemma4                    # LLM 模型
ollama pull snowflake-arctic-embed2   # Embedding 模型

# 启动服务
ollama serve
```

## 使用方式

### 1. 命令行界面

```bash
# 文本生成
langchain-cli generate "你好，请介绍一下你自己" --model ollama/gemma4

# 聊天模式
langchain-cli chat --model ollama/gemma4

# 导入文档到 RAG 知识库
langchain-import ./docs '*.md'
```

### 2. Web UI (Streamlit)

```bash
# 启动 Web 界面
langchain-cli web
# 或
make web
```

访问 http://localhost:8501 使用 Web 界面。

### 3. API 服务

```bash
# 启动 API 服务
langchain-api
# 或
make api
```

API 文档：http://localhost:8000/docs

### 4. Python API

```python
from langchain_llm_toolkit.llm_integration import LLMIntegration
from langchain_llm_toolkit.rag import RAGSystem

# LLM 使用
llm = LLMIntegration(model="ollama/gemma4")
response = llm.generate("你好")
print(response)

# 流式输出
for chunk in llm.generate_stream("讲个故事"):
    print(chunk, end="", flush=True)

# RAG 系统
rag = RAGSystem()
rag.load_vector_store()
answer, docs = rag.generate_answer("什么是 LangChain？")
print(answer)
```

## API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v1/generate` | POST | 文本生成 |
| `/api/v1/chat` | POST | 聊天对话 |
| `/api/v1/generate/stream` | POST | 流式生成 |
| `/api/v1/rag/query` | POST | RAG 查询 |
| `/api/v1/rag/upload` | POST | 上传文档 |
| `/api/v1/models` | GET | 获取模型列表 |
| `/api/v1/conversations` | GET | 获取对话列表 |
| `/api/v1/auth/login` | POST | 用户登录 |

## 推荐模型

### LLM 模型

| 模型 | 大小 | 说明 |
|------|------|------|
| gemma4 | 9.6 GB | 推荐，效果好 |
| llama3.1:8b | 4.7 GB | 平衡选择 |
| deepseek-r1:7b | 4.7 GB | 推理能力强 |

### Embedding 模型

| 模型 | 大小 | Context | 维度 | 说明 |
|------|------|---------|------|------|
| snowflake-arctic-embed2 | 1.2 GB | 8192 | 1024 | 推荐，多语言 |
| nomic-embed-text | 274 MB | 8192 | 768 | 轻量选择 |

## 开发

### 运行测试

```bash
# 运行所有测试
make test

# 运行测试并查看覆盖率
make test-coverage
```

### 代码质量

```bash
# 格式化代码
make format

# 代码检查
make lint
```

### Makefile 命令

```bash
make help          # 查看所有命令
make install       # 安装依赖
make test          # 运行测试
make format        # 格式化代码
make lint          # 代码检查
make web           # 启动 Web UI
make api           # 启动 API 服务
make clean         # 清理缓存
```

## 测试覆盖率

当前测试覆盖率：**38%**

| 模块 | 覆盖率 |
|------|--------|
| api.py | 69% |
| llm_integration.py | 72% |
| rag.py | 55% |
| cache.py | 64% |
| performance.py | 64% |

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 贡献

欢迎贡献！请查看 [CONTRIBUTING.md](docs/CONTRIBUTING.md) 了解详情。
