# LangChain LLM Toolkit

一个基于 LangChain 和 LiteLLM 的完整 LLM 工具集，支持文本生成、聊天对话和 RAG 文档问答功能。

## 功能特性

- **多模型集成**：使用 LiteLLM 调用各种 AI 模型（OpenAI、Anthropic、Google、Ollama 等）
- **文本生成**：支持基本文本生成和聊天模式
- **参数配置**：可配置模型参数（温度、最大 tokens 等）
- **RAG 系统**：实现检索增强生成，基于文档内容生成准确回答
- **文档处理**：支持加载和处理多种格式的文档（PDF、TXT、DOCX）
- **向量存储**：使用 FAISS 实现高效的文档检索
- **命令行界面**：提供便捷的终端操作方式

## 项目结构

```
langchain-llm-toolkit/
├── config/                # 配置文件目录
│   ├── __init__.py
│   └── settings.py        # 项目配置
├── vector_store/          # 向量存储目录
├── __pycache__/           # Python 缓存文件
├── venv/                  # 虚拟环境
├── .env                   # 环境变量文件
├── README.md              # 项目文档
├── cli.py                 # 命令行界面
├── conversation.py        # 对话管理
├── document_loader.py     # 文档加载器
├── llm_integration.py     # LLM 集成
├── rag.py                 # RAG 系统
├── requirements.txt       # 依赖项
├── test_config.py         # 配置测试
├── test_document.txt      # 测试文档
├── test_document_processing.py  # 文档处理测试
└── text_splitter.py       # 文本分割器
```

## 安装和设置

本项目使用 **uv** 作为包管理工具，这是目前最现代化的 Python 包管理方案，具有极快的速度和优秀的依赖管理能力。

### 为什么选择 uv？

- ⚡ **极快的速度**：使用 Rust 编写，比 pip 快 10-100 倍
- 🔒 **可靠的依赖管理**：自动生成 `uv.lock` 锁定文件
- 🎯 **统一工具链**：集成了虚拟环境、包管理、脚本运行等功能
- 📦 **兼容性好**：完全兼容 `pyproject.toml` 和 `requirements.txt`

### 安装 uv

如果还没有安装 uv，请先安装：

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# 或者使用 Homebrew
brew install uv

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 使用 Makefile 快速设置（推荐）

```bash
# 查看所有可用命令
make help

# 一键设置项目（安装依赖、创建 .env 文件）
make all

# 或者分步执行：
make install     # 安装依赖（使用 uv）
make env         # 创建 .env 文件
```

### 手动安装

#### 1. 克隆项目

```bash
git clone <repository-url>
cd langchain-llm-toolkit
```

#### 2. 安装依赖

```bash
# 使用 uv 安装依赖（推荐）
uv sync

# 或者使用传统方式
pip install -r requirements.txt
```

#### 3. 配置环境变量

1. 创建 `.env` 文件：

```bash
cp .env.example .env  # 如果 .env.example 存在
# 或直接创建 .env 文件
```

2. 在 `.env` 文件中设置你的 API 密钥：

```env
# API Keys
OPENAI_API_KEY=your_openai_api_key
# ANTHROPIC_API_KEY=your_anthropic_api_key
# GOOGLE_API_KEY=your_google_api_key
# HUGGINGFACE_API_KEY=your_huggingface_api_key
# LANGSMITH_API_KEY=your_langsmith_api_key

# Model Settings
DEFAULT_MODEL=gpt-4o
DEFAULT_TEMPERATURE=0.7

# Ollama Settings (本地模型)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3

# Application Settings
APP_NAME=LangChain LLM Toolkit
DEBUG=False
```

### 4. 使用 Ollama 本地模型

如果你想使用 Ollama 本地模型，需要先安装 Ollama 并下载模型：

1. **安装 Ollama**：
   - 访问 [Ollama 官网](https://ollama.com/) 下载并安装适合你操作系统的版本
   - 安装完成后，Ollama 服务会自动启动

2. **下载模型**：
   - 打开终端，运行以下命令下载模型：
     ```bash
     # 下载 llama3 模型
     ollama pull llama3
     
     # 或者下载其他模型
     ollama pull mistral
     ollama pull phi3
     ollama pull gemma
     ```

3. **使用 Ollama 模型**：
   - 在代码中使用 `ollama/` 前缀指定 Ollama 模型：
     ```python
     from llm_integration import LLMIntegration
     
     llm = LLMIntegration()
     # 使用 Ollama 的 llama3 模型
     llm.set_model("ollama/llama3")
     
     # 生成文本
     response = llm.generate("Hello, who are you?")
     print(response)
     ```
   
   - 或者在 CLI 中使用：
     ```bash
     # 使用 Ollama 模型生成文本
     ./cli.py generate "Hello, who are you?" --model ollama/llama3
     
     # 使用 Ollama 模型进入聊天模式
     ./cli.py chat --model ollama/llama3
     ```

## 核心组件

### 1. LLM 集成 (llm_integration.py)

提供统一的 LLM 接口，支持多种 AI 模型。

**主要功能**：
- 文本生成：根据提示生成文本响应
- 聊天模式：支持多轮对话
- 模型切换：可以在运行时切换不同的 AI 模型
- 参数调整：可以调整温度等生成参数
- **日志记录**：完整的日志记录系统，便于调试和监控
- **错误重试**：自动重试失败的请求（最多 3 次）
- **输入验证**：验证输入提示和消息的有效性
- **流式输出**：支持流式生成文本（仅 Ollama）
- **超时控制**：可配置的请求超时时间

### 2. 文档加载器 (document_loader.py)

负责加载和处理不同格式的文档。

**支持的格式**：
- PDF：使用 pypdf 库提取文本
- TXT：直接读取文本文件
- DOCX：使用 python-docx 库提取文本

### 3. 文本分割器 (text_splitter.py)

将长文本分割为更小的片段，以便于向量存储和检索。

**分割方法**：
- 递归字符分割：根据自然分隔符（段落、句子、单词）进行分割
- 字符分割：简单的字符计数分割

### 4. RAG 系统 (rag.py)

实现检索增强生成功能，结合文档检索和 LLM 生成。

**主要功能**：
- 文档处理：加载和分割文档
- 向量存储：创建和管理向量数据库（支持 Qdrant 和 FAISS）
- 文档检索：基于相似度搜索相关文档
- 生成回答：基于检索到的文档生成准确回答
- 存储管理：保存和加载向量存储

**向量数据库支持**：
- **Qdrant（推荐）**：高性能向量数据库，支持持久化和更好的性能
- **FAISS**：轻量级向量存储，适合小型项目

## 使用示例

### 1. 基本 LLM 使用

```python
from llm_integration import LLMIntegration

# 初始化集成（可配置超时和重试次数）
llm = LLMIntegration(timeout=30, max_retries=3)

# 生成文本
response = llm.generate("Hello, who are you?")
print(response)

# 流式生成（仅 Ollama）
llm.set_model("ollama/gemma3")
for chunk in llm.generate_stream("Tell me a story"):
    print(chunk, end="", flush=True)

# 聊天模式
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What's the capital of France?"}
]
response = llm.chat(messages)
print(response)

# 设置模型和参数
llm.set_model("gpt-4o")
llm.set_temperature(0.7)
llm.set_timeout(60)

# 输入验证示例
try:
    llm.generate("")  # 会抛出 ValueError
except ValueError as e:
    print(f"验证错误: {e}")
```

# 聊天模式
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What's the capital of France?"}
]
response = llm.chat(messages)
print(response)

# 切换模型
llm.set_model("gpt-3.5-turbo")

# 使用 Ollama 本地模型
llm.set_model("ollama/llama3")

# 调整温度参数
llm.set_temperature(0.1)
```

### 2. RAG 系统使用

#### 环境变量配置

在 `.env` 文件中配置存储路径：

```bash
# 向量存储类型（faiss, qdrant）
VECTOR_STORE_TYPE=qdrant

# Qdrant 存储路径（本地模式）
RAG_QDRANT_PATH=./qdrant_storage

# FAISS 存储路径
RAG_FAISS_PATH=./vector_store

# 集合名称
RAG_COLLECTION_NAME=langchain_documents
```

#### 基本使用

```python
from rag import RAGSystem

# 初始化 RAG 系统（默认使用 Qdrant，路径从环境变量读取）
rag_system = RAGSystem(vector_store_type="qdrant")

# 或使用 FAISS
# rag_system = RAGSystem(vector_store_type="faiss")

# 或自定义存储路径
# rag_system = RAGSystem(
#     vector_store_type="qdrant",
#     qdrant_persist_dir="/custom/path/qdrant",
#     collection_name="my_documents"
# )

# 加载文档
documents = rag_system.load_and_process_documents(["test_document.txt"])

# 创建向量存储
rag_system.create_vector_store(documents)

# 保存向量存储（Qdrant 自动持久化，FAISS 需要手动保存）
rag_system.save_vector_store()

# 加载向量存储
rag_system.load_vector_store()

# 获取向量存储信息（仅 Qdrant）
info = rag_system.get_collection_info()
print(f"向量存储信息: {info}")

# 生成基于文档的回答
query = "LangChain 的主要组件有哪些？"
answer, relevant_docs = rag_system.generate_answer(query)
print(f"问题: {query}")
print(f"回答: {answer}")
print("\n相关文档:")
for i, doc in enumerate(relevant_docs):
    print(f"{i+1}. {doc.page_content[:100]}...")
```

### 3. 文档加载和处理

```python
from document_loader import DocumentLoader
from text_splitter import TextSplitter

# 初始化文档加载器
loader = DocumentLoader()

# 加载文档
documents = loader.load_document("example.pdf")
print(f"加载了 {len(documents)} 个文档")

# 初始化文本分割器
splitter = TextSplitter()

# 分割文档
split_docs = splitter.split_documents(documents, chunk_size=500, chunk_overlap=100)
print(f"分割后得到 {len(split_docs)} 个文档片段")

# 查看分割结果
for i, doc in enumerate(split_docs[:3]):
    print(f"\n片段 {i+1}:")
    print(doc.page_content[:200] + "...")
```

### 4. 命令行界面 (CLI)

项目提供了命令行界面，方便直接从终端使用 LLM 功能。

#### 基本用法

```bash
# 激活虚拟环境
source venv/bin/activate

# 查看帮助信息
./cli.py --help

# 生成文本
./cli.py generate "Hello, who are you?"

# 生成文本（指定模型和温度）
./cli.py generate "Hello, who are you?" --model gpt-3.5-turbo --temperature 0.7

# 使用 Ollama 模型生成文本
./cli.py generate "Hello, who are you?" --model ollama/llama3

# 进入聊天模式
./cli.py chat

# 聊天模式（指定模型和温度）
./cli.py chat --model gpt-4o --temperature 0.5

# 使用 Ollama 模型进入聊天模式
./cli.py chat --model ollama/llama3

# 列出支持的模型
./cli.py model list

# 设置默认模型
./cli.py model set gpt-4o

# 设置温度参数
./cli.py temperature set 0.7
```

### 6. 日志配置

项目内置了完整的日志系统，便于调试和监控。

```python
from logger import setup_logging

# 配置日志（输出到控制台）
setup_logging(log_level="INFO")

# 配置日志（输出到文件）
setup_logging(log_level="DEBUG", log_file="logs/app.log")

# 使用日志
import logging
logger = logging.getLogger("langchain_project")

logger.debug("调试信息")
logger.info("一般信息")
logger.warning("警告信息")
logger.error("错误信息")
```

**日志级别**：
- `DEBUG`: 详细的调试信息
- `INFO`: 一般信息（默认）
- `WARNING`: 警告信息
- `ERROR`: 错误信息
- `CRITICAL`: 严重错误

**日志文件**：
- 自动轮转（10MB 一个文件）
- 保留最近 5 个文件
- 自动创建日志目录

#### 聊天模式使用

在聊天模式中，你可以：
1. 输入系统提示（可选）
2. 输入消息与 AI 对话
3. 输入 'exit' 退出聊天模式

### 5. Web 界面 (Streamlit)

项目提供了基于 Streamlit 的 Web 界面，提供更友好的交互体验。

#### 启动 Web 界面

```bash
# 使用默认配置启动
make web

# 或直接运行
uv run streamlit run app.py

# 指定端口启动
make web-port PORT=8080

# 允许外部访问（局域网）
make web-external
```

#### Web 界面功能

1. **智能对话模式**
   - 多轮对话
   - 支持多种模型切换
   - 可调节温度参数
   - 实时对话历史

2. **RAG 文档问答模式**
   - 上传 PDF、TXT、DOCX 文档
   - 基于文档内容回答问题
   - 显示相关文档片段
   - 支持多文档处理

3. **模型配置**
   - 支持 Ollama 本地模型
   - 支持 OpenAI 模型
   - 实时切换模型
   - 可调节生成参数

### 6. FastAPI 服务

项目提供了基于 FastAPI 的 RESTful API 服务，支持程序化访问。

#### 启动 API 服务

```bash
# 使用默认配置启动
make api

# 或直接运行
uv run uvicorn api:app --reload

# 指定端口启动
make api-port PORT=8080

# 允许外部访问
make api-external
```

#### API 文档

启动 API 服务后，可以访问自动生成的 API 文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

#### API 端点

**1. 健康检查**
```bash
GET /
GET /health
```

**2. 文本生成**
```bash
POST /api/v1/generate
Content-Type: application/json

{
  "prompt": "你好，请介绍一下你自己",
  "model": "ollama/gemma3",
  "temperature": 0.7,
  "timeout": 30
}
```

**3. 聊天模式**
```bash
POST /api/v1/chat
Content-Type: application/json

{
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What's the capital of France?"}
  ],
  "model": "ollama/gemma3",
  "temperature": 0.7
}
```

**4. RAG 查询**
```bash
POST /api/v1/rag/query
Content-Type: application/json

{
  "query": "LangChain 的主要组件有哪些？",
  "k": 3
}
```

**5. RAG 文档上传**
```bash
POST /api/v1/rag/upload
Content-Type: multipart/form-data

file: document.pdf
```

**6. 获取模型列表**
```bash
GET /api/v1/models
```

**7. RAG 系统信息**
```bash
GET /api/v1/rag/info
```

**8. 清空 RAG 向量存储**
```bash
DELETE /api/v1/rag/clear
```

#### 使用示例

**Python 调用示例**：
```python
import requests

# 文本生成
response = requests.post(
    "http://localhost:8000/api/v1/generate",
    json={
        "prompt": "你好",
        "model": "ollama/gemma3"
    }
)
print(response.json())

# RAG 查询
response = requests.post(
    "http://localhost:8000/api/v1/rag/query",
    json={"query": "什么是 LangChain？"}
)
print(response.json())
```

**JavaScript 调用示例**：
```javascript
// 文本生成
fetch('http://localhost:8000/api/v1/generate', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    prompt: '你好',
    model: 'ollama/gemma3'
  })
})
.then(res => res.json())
.then(data => console.log(data));
```

**curl 调用示例**：
```bash
# 文本生成
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "你好", "model": "ollama/gemma3"}'

# 获取模型列表
curl http://localhost:8000/api/v1/models
```

#### 使用示例

1. **启动 Web 界面**
   ```bash
   make web
   ```

2. **在浏览器中访问**
   ```
   http://localhost:8501
   ```

3. **选择功能模式**
   - 智能对话：直接与 AI 对话
   - RAG 文档问答：上传文档后提问

4. **配置模型**
   - 在侧边栏选择模型
   - 调整温度参数
   - 开始对话

## Makefile 命令参考

项目提供了 Makefile 来简化常用操作，所有命令都使用 uv 执行：

```bash
# 查看所有可用命令
make help

# 项目设置
make install       # 安装依赖（使用 uv sync）
make sync          # 同步依赖到虚拟环境
make env           # 创建 .env 文件
make lock          # 锁定依赖版本（生成 uv.lock）
make all           # 一键设置项目（推荐）

# 运行测试
make test          # 运行所有测试
make test-llm      # 测试 LLM 集成
make test-rag      # 测试 RAG 系统
make test-doc      # 测试文档处理
make test-conversation  # 测试对话管理

# 使用 CLI
make run           # 运行 CLI 工具
make chat          # 进入聊天模式
make generate PROMPT="你的提示"  # 生成文本

# 代码质量
make format        # 格式化代码（使用 black）
make lint          # 代码检查（使用 flake8）

# 清理
make clean         # 清理缓存和临时文件
```

### uv 常用命令

```bash
# 安装依赖
uv sync

# 添加新依赖
uv add package-name

# 添加开发依赖
uv add --dev package-name

# 运行 Python 脚本
uv run python script.py

# 运行 CLI 命令
uv run python cli.py --help

# 更新所有依赖
uv sync --upgrade

# 创建虚拟环境（自动）
uv venv
```

## 运行测试

### 1. 测试 LLM 集成

```bash
# 在虚拟环境中运行测试
./venv/bin/python llm_integration.py
```

### 2. 测试 RAG 系统

```bash
# 在虚拟环境中运行测试
./venv/bin/python rag.py
```

### 3. 测试文档处理

```bash
# 在虚拟环境中运行测试
./venv/bin/python test_document_processing.py
```

## 开发工具

### 代码风格配置

项目使用 `.editorconfig` 统一不同编辑器的代码风格配置：

- **字符编码**: UTF-8
- **换行符**: LF
- **Python 缩进**: 4 空格
- **YAML/JSON 缩进**: 2 空格

### Pre-commit Hooks

项目配置了 pre-commit hooks 用于自动代码检查：

```bash
# 安装 pre-commit
pip install pre-commit

# 初始化 hooks
pre-commit install

# 手动运行所有检查
pre-commit run --all-files
```

**配置的检查项：**
- Black 代码格式化
- Flake8 代码检查
- MyPy 类型检查
- Bandit 安全检查
- 导入排序 (isort)
- 文件格式检查

### CI/CD (GitHub Actions)

项目配置了自动化 CI/CD 流程：

**触发条件：**
- Push 到 main/develop 分支
- Pull Request 到 main/develop 分支

**工作流程：**
1. **测试作业** - 多 Python 版本测试 (3.11, 3.12, 3.13)
2. **安全检查** - Bandit 安全扫描
3. **构建作业** - 打包发布

**查看状态：**
- 在 GitHub 仓库的 Actions 标签页查看运行状态
- 测试覆盖率自动上传到 Codecov

## 支持的模型

- **OpenAI**：gpt-4o, gpt-4, gpt-3.5-turbo
- **Anthropic**：claude-3-opus, claude-3-sonnet
- **Google**：gemini-pro
- **Ollama**：llama3, mistral, phi3, gemma 等本地模型
- **以及其他 LiteLLM 支持的模型**

## 常见问题和解决方案

### 1. API 密钥错误

**问题**：运行时出现 API 密钥错误

**解决方案**：
- 确保在 `.env` 文件中正确设置了 API 密钥
- 确保使用的模型与设置的 API 密钥匹配
- 检查网络连接是否正常

### 2. 文档加载失败

**问题**：无法加载特定格式的文档

**解决方案**：
- 确保安装了相应的依赖库（pypdf for PDF, python-docx for DOCX）
- 检查文件路径是否正确
- 检查文件是否损坏

### 3. 向量存储错误

**问题**：创建或加载向量存储时出错

**解决方案**：
- 确保 FAISS 库已正确安装
- 检查向量存储路径是否存在且可写
- 对于大型文档，考虑调整 chunk_size 参数

### 4. Ollama 模型错误

**问题**：运行时出现 Ollama 相关错误，如 "model not found"

**解决方案**：
- 确保 Ollama 服务正在运行（可以通过 `ollama list` 命令检查）
- 确保已下载所需的模型（使用 `ollama pull <model_name>` 命令）
- 检查 OLLAMA_BASE_URL 是否正确设置（默认为 http://localhost:11434）
- 确保使用正确的模型名称格式：`ollama/<model_name>`

## 性能优化

1. **模型选择**：根据任务复杂度选择合适的模型
2. **参数调优**：根据需要调整温度、最大 tokens 等参数
3. **文档处理**：对于大型文档，适当调整 chunk_size 和 chunk_overlap
4. **向量存储**：定期更新向量存储以包含最新文档
5. **缓存**：考虑实现请求缓存以减少重复 API 调用

## 扩展建议

1. **添加更多文档格式支持**：如 Markdown、HTML 等
2. **实现更高级的 RAG 策略**：如混合检索、重排序等
3. **添加用户界面**：开发 Web 或桌面应用
4. **集成更多模型**：如开源模型、本地模型等
5. **添加评估功能**：评估生成结果的质量和准确性

## 注意事项

- 你需要在 `.env` 文件中设置相应的 API 密钥才能使用对应服务商的模型
- 不同模型的参数可能有所不同，请参考 LiteLLM 文档进行调整
- 大规模使用时请注意 API 调用费用
- 对于生产环境，建议添加更完善的错误处理和日志记录
- 请遵守各模型提供商的使用条款和限制