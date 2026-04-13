# OpenClaw 快速命令参考

## 🚀 项目初始化（首次使用）

```bash
cd /Users/erishen/Workspace/TraeSolo/langchain-llm-toolkit
make all
# 然后编辑 .env 文件设置 API 密钥
```

## 📝 常用命令速查表

### 文本生成
```bash
# 基本生成
uv run python cli.py generate "你的提示"

# 指定模型
uv run python cli.py generate "你的提示" --model gpt-4o

# 使用本地模型
uv run python cli.py generate "你的提示" --model ollama/llama3

# Makefile 快捷方式
make generate PROMPT="你的提示"
```

### 聊天模式
```bash
# 进入聊天
uv run python cli.py chat

# 指定模型聊天
uv run python cli.py chat --model gpt-4o --temperature 0.7

# Makefile 快捷方式
make chat
```

### 测试
```bash
make test              # 运行所有测试
make test-coverage     # 测试 + 覆盖率报告
```

### 服务启动
```bash
make web               # Web 界面（http://localhost:8501）
make api               # API 服务（http://localhost:8000）
```

### 代码质量
```bash
make check             # 运行所有检查
make format            # 格式化代码
make lint              # 代码检查
```

## 🎯 核心模块快速导入

```python
# LLM 集成
from llm_integration import LLMIntegration
llm = LLMIntegration()
response = llm.generate("你好")

# 对话管理
from conversation import ConversationManager
manager = ConversationManager()
response = manager.converse("你好")

# RAG 系统
from rag import RAGSystem
rag = RAGSystem(vector_store_type="faiss")
```

## 🔧 API 端点

启动 API: `make api`

- 文档: http://localhost:8000/docs
- 生成: POST /api/v1/generate
- 聊天: POST /api/v1/chat
- RAG查询: POST /api/v1/rag/query

## 📦 支持的模型

- OpenAI: gpt-4o, gpt-4, gpt-3.5-turbo
- Anthropic: claude-3-opus, claude-3-sonnet
- Google: gemini-pro
- Ollama: ollama/llama3, ollama/mistral, ollama/gemma

## ⚠️ 重要提示

1. **必须设置 .env 文件**: 复制 .env.example 并填写 API 密钥
2. **使用 uv 命令**: 所有命令都通过 `uv run` 或 `make` 执行
3. **Ollama 模型**: 需要先 `ollama pull <model_name>` 下载模型

## 📊 项目状态

- 测试覆盖率: 85%
- 测试数量: 259 个
- Python 版本: 3.11+
- 包管理器: uv

## 🆘 故障排除

```bash
# 清理并重装
make clean-all
make all

# 检查 Ollama
ollama list

# 查看详细帮助
make help
```

---

详细文档: [OPENCLAW_GUIDE.md](./OPENCLAW_GUIDE.md) | 完整文档: [README.md](./README.md)
