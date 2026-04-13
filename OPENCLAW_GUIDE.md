# OpenClaw 龙虾助理使用指南

本文档专门为 OpenClaw 龙虾助理准备，帮助您快速理解和使用 langchain-llm-toolkit 项目。

## 📋 项目概述

**项目名称**: LangChain LLM Toolkit  
**项目类型**: 基于 LangChain 和 LiteLLM 的 LLM 应用框架  
**主要功能**: 文本生成、聊天对话、RAG 文档问答  
**包管理器**: uv（现代化 Python 包管理工具）  
**Python 版本**: 3.11+

## 🚀 快速开始命令

### 1. 项目初始化
```bash
# 进入项目目录
cd /Users/erishen/Workspace/TraeSolo/langchain-llm-toolkit

# 一键设置项目（清理 + 安装依赖 + 配置环境）
make all

# 或者分步执行
make install    # 安装依赖
make env        # 创建 .env 文件
```

### 2. 配置 API 密钥
编辑 `.env` 文件，设置必要的 API 密钥：
```bash
# OpenAI API（如果使用 OpenAI 模型）
OPENAI_API_KEY=your_openai_api_key

# 默认模型配置
DEFAULT_MODEL=gpt-4o
DEFAULT_TEMPERATURE=0.7

# Ollama 本地模型配置（如果使用本地模型）
OLLAMA_BASE_URL=http://localhost:11434
```

## 🛠️ 主要 CLI 命令

### 文本生成
```bash
# 基本生成
uv run python cli.py generate "你好，请介绍一下你自己"

# 指定模型生成
uv run python cli.py generate "Hello" --model gpt-4o

# 使用 Ollama 本地模型
uv run python cli.py generate "你好" --model ollama/llama3

# 使用 Makefile 快捷命令
make generate PROMPT="你好"
```

### 聊天模式
```bash
# 进入聊天模式
uv run python cli.py chat

# 指定模型和温度
uv run python cli.py chat --model gpt-4o --temperature 0.7

# 使用 Ollama 模型聊天
uv run python cli.py chat --model ollama/gemma3

# 使用 Makefile 快捷命令
make chat
```

### 模型管理
```bash
# 列出支持的模型
uv run python cli.py model list

# 设置默认模型
uv run python cli.py model set gpt-4o

# 使用 Makefile
make model-list
```

### 温度参数管理
```bash
# 设置温度
uv run python cli.py temperature set 0.7

# 获取当前温度
uv run python cli.py temperature get
```

## 📦 Makefile 常用命令

### 测试相关
```bash
make test              # 运行所有测试
make test-llm          # 测试 LLM 集成
make test-rag          # 测试 RAG 系统
make test-coverage     # 运行测试并生成覆盖率报告
```

### 代码质量
```bash
make format            # 格式化代码（black）
make lint              # 代码检查（flake8）
make type-check        # 类型检查（mypy）
make security-check    # 安全检查（bandit）
make check             # 运行所有检查
```

### Web 和 API 服务
```bash
make web               # 启动 Streamlit Web 界面（端口 8501）
make web-port PORT=8080  # 指定端口启动 Web 界面
make api               # 启动 FastAPI 服务（端口 8000）
make api-port PORT=8080  # 指定端口启动 API 服务
```

### 清理
```bash
make clean             # 清理缓存和临时文件
make clean-all         # 深度清理（包括虚拟环境）
```

## 🏗️ 项目结构

```
langchain-llm-toolkit/
├── cli.py                 # 命令行界面（主要入口）
├── llm_integration.py     # LLM 集成（核心模块）
├── conversation.py        # 对话管理
├── rag.py                 # RAG 系统
├── document_loader.py     # 文档加载器
├── text_splitter.py       # 文本分割器
├── prompt_templates.py    # 提示模板
├── api.py                 # FastAPI 服务
├── app.py                 # Streamlit Web 应用
├── logger.py              # 日志系统
├── config/                # 配置目录
│   ├── settings.py        # 项目配置
│   └── __init__.py
├── models/                # 数据模型
│   ├── schemas.py         # Pydantic 模型
│   └── __init__.py
├── Makefile               # Make 命令
├── pyproject.toml         # 项目配置
├── requirements.txt       # 依赖列表
├── .env                   # 环境变量（需创建）
└── .env.example           # 环境变量示例
```

## 🎯 核心功能模块

### 1. LLM 集成 (llm_integration.py)
**功能**: 统一的 LLM 接口，支持多种 AI 模型

**支持的模型**:
- OpenAI: gpt-4o, gpt-4, gpt-3.5-turbo
- Anthropic: claude-3-opus, claude-3-sonnet
- Google: gemini-pro
- Ollama 本地模型: llama3, mistral, phi3, gemma

**主要方法**:
- `generate(prompt)`: 生成文本响应
- `chat(messages)`: 聊天模式
- `generate_stream(prompt)`: 流式生成（仅 Ollama）
- `set_model(model)`: 设置模型
- `set_temperature(temp)`: 设置温度参数

### 2. 对话管理 (conversation.py)
**功能**: 管理多轮对话历史

**主要方法**:
- `converse(user_input)`: 进行对话
- `get_history()`: 获取对话历史
- `clear_history()`: 清空历史
- `set_model(model)`: 设置模型
- `set_temperature(temp)`: 设置温度

### 3. RAG 系统 (rag.py)
**功能**: 检索增强生成，基于文档回答问题

**主要方法**:
- `load_and_process_documents(file_paths)`: 加载文档
- `create_vector_store(documents)`: 创建向量存储
- `generate_answer(query)`: 基于文档生成回答
- `save_vector_store(path)`: 保存向量存储
- `load_vector_store(path)`: 加载向量存储

**支持的文档格式**: PDF, TXT, DOCX

### 4. 文档加载器 (document_loader.py)
**功能**: 加载和处理不同格式的文档

**主要方法**:
- `load_document(file_path)`: 加载文档

### 5. 文本分割器 (text_splitter.py)
**功能**: 将长文本分割为更小的片段

**主要方法**:
- `split_documents(documents)`: 分割文档

## 💡 使用示例

### Python 代码示例

#### 1. 基本 LLM 使用
```python
from llm_integration import LLMIntegration

# 初始化
llm = LLMIntegration()

# 生成文本
response = llm.generate("你好，请介绍一下你自己")
print(response)

# 聊天模式
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What's the capital of France?"}
]
response = llm.chat(messages)
print(response)

# 切换模型
llm.set_model("gpt-4o")
llm.set_temperature(0.7)
```

#### 2. RAG 文档问答
```python
from rag import RAGSystem

# 初始化 RAG 系统
rag = RAGSystem(vector_store_type="faiss")

# 加载文档
documents = rag.load_and_process_documents(["document.pdf", "notes.txt"])

# 创建向量存储
rag.create_vector_store(documents)

# 生成回答
answer, relevant_docs = rag.generate_answer("文档的主要内容是什么？")
print(f"回答: {answer}")
```

#### 3. 对话管理
```python
from conversation import ConversationManager

# 初始化对话管理器
manager = ConversationManager()

# 设置模型
manager.set_model("gpt-4o")

# 进行对话
response1 = manager.converse("你好")
response2 = manager.converse("我刚才说了什么？")

# 查看历史
history = manager.get_history()
```

## 🔧 API 服务使用

### 启动 API 服务
```bash
make api
# API 地址: http://localhost:8000
# API 文档: http://localhost:8000/docs
```

### API 端点示例

#### 文本生成
```bash
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "你好", "model": "gpt-4o"}'
```

#### 聊天模式
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "你好"}
    ],
    "model": "gpt-4o"
  }'
```

#### RAG 查询
```bash
curl -X POST http://localhost:8000/api/v1/rag/query \
  -H "Content-Type: application/json" \
  -d '{"query": "什么是 LangChain？", "k": 3}'
```

## 🌐 Web 界面使用

### 启动 Web 界面
```bash
make web
# 访问地址: http://localhost:8501
```

### Web 界面功能
1. **智能对话模式**: 多轮对话，支持多种模型
2. **RAG 文档问答**: 上传文档后提问
3. **模型配置**: 实时切换模型和参数

## ⚠️ 注意事项

### 1. 环境配置
- 必须先创建 `.env` 文件并设置 API 密钥
- 使用 OpenAI 模型需要 `OPENAI_API_KEY`
- 使用 Ollama 本地模型需要先安装 Ollama 并下载模型

### 2. Ollama 使用
```bash
# 安装 Ollama（如果使用本地模型）
# 访问 https://ollama.com/ 下载安装

# 下载模型
ollama pull llama3
ollama pull gemma3

# 检查 Ollama 服务
ollama list
```

### 3. 依赖管理
- 项目使用 `uv` 作为包管理器
- 所有命令都应该使用 `uv run` 或通过 Makefile 执行
- 不要直接使用 pip，使用 `uv add` 添加依赖

### 4. 测试覆盖率
- 当前测试覆盖率: 85%
- 测试数量: 259 个
- 运行测试: `make test` 或 `make test-coverage`

## 📊 项目状态

### 测试覆盖率详情
| 模块 | 覆盖率 | 状态 |
|------|--------|------|
| llm_integration.py | 74% | ✅ 良好 |
| conversation.py | 44% | ⚠️ 需改进 |
| document_loader.py | 52% | ⚠️ 需改进 |
| rag.py | 52% | ⚠️ 需改进 |
| logger.py | 100% | ✅ 优秀 |
| text_splitter.py | 100% | ✅ 优秀 |

### 代码质量
- ✅ 类型检查通过（mypy）
- ✅ 代码格式化通过（black）
- ✅ 代码检查通过（flake8）
- ✅ 安全检查通过（bandit）

## 🎓 学习资源

### 项目文档
- [README.md](./README.md) - 完整项目文档
- [API 文档](http://localhost:8000/docs) - FastAPI 自动文档

### 外部资源
- [LangChain 官方文档](https://python.langchain.com/)
- [LiteLLM 文档](https://docs.litellm.ai/)
- [Ollama 官网](https://ollama.com/)

## 🐛 常见问题

### 1. API 密钥错误
**问题**: 运行时提示 API 密钥错误  
**解决**: 检查 `.env` 文件中的 API 密钥是否正确设置

### 2. Ollama 模型未找到
**问题**: 提示 "model not found"  
**解决**: 
```bash
ollama list              # 检查已下载的模型
ollama pull llama3       # 下载模型
```

### 3. 依赖安装失败
**问题**: uv 安装依赖失败  
**解决**:
```bash
make clean-all           # 清理所有文件
make all                 # 重新安装
```

### 4. 测试失败
**问题**: 某些测试失败  
**解决**:
```bash
make test-coverage       # 运行测试并查看详细报告
```

## 📝 快速参考卡

### 最常用命令
```bash
# 项目设置
make all                 # 一键设置

# 生成文本
uv run python cli.py generate "你的提示"

# 聊天模式
uv run python cli.py chat

# 运行测试
make test

# 启动 Web
make web

# 启动 API
make api

# 查看帮助
make help
```

### Python 快速使用
```python
# 导入核心模块
from llm_integration import LLMIntegration
from conversation import ConversationManager
from rag import RAGSystem

# 快速生成
llm = LLMIntegration()
response = llm.generate("你好")

# 快速聊天
manager = ConversationManager()
response = manager.converse("你好")

# 快速 RAG
rag = RAGSystem(vector_store_type="faiss")
```

---

**文档版本**: 1.0  
**最后更新**: 2026-04-13  
**维护者**: OpenClaw 龙虾助理团队

如有任何问题，请参考 [README.md](./README.md) 或查看项目源码。
