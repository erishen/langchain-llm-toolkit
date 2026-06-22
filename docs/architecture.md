# langchain-llm-toolkit 架构文档

## 概述

langchain-llm-toolkit 是一个基于 LangChain 和 LiteLLM 的 LLM 工具集，提供命令行、REST API 和 Web UI 三种交互方式。核心能力包括：

- **RAG 系统**：FAISS 本地向量存储 + BM25 关键词 + 语义向量混合检索
- **多模型支持**：通过 LiteLLM 统一接入 DeepSeek/OpenAI/Anthropic/Google 等云端模型，以及 Ollama 本地模型
- **完整工具链**：文档加载、文本分割、对话管理、Agent 系统、Token 成本追踪、速率限制

**核心理念**：本地优先、隐私保护——嵌入和向量存储完全在本地运行，不依赖外部嵌入 API。

## 架构总览

```
┌─────────────────────────────────────────────────────────────┐
│                        入口层                               │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────────┐     │
│  │ CLI      │  │ FastAPI       │  │ Streamlit Web UI  │     │
│  │ (Typer)  │  │ (25 endpoints)│  │ (5-page SPA)      │     │
│  └────┬─────┘  └──────┬───────┘  └────────┬──────────┘     │
└───────┼───────────────┼───────────────────┼────────────────┘
        │               │                   │
        ▼               ▼                   ▼
┌─────────────────────────────────────────────────────────────┐
│                      核心服务层                              │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ RAGSystem    │  │LLMIntegration│  │ AuthManager  │      │
│  │ (检索+生成)  │  │ (多模型调用)  │  │ (JWT+APIKey) │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                 │                 │               │
│  ┌──────┴───────┐  ┌──────┴───────┐  ┌──────┴───────┐      │
│  │HybridRetrieve│  │ LiteLLM      │  │ AuthStore    │      │
│  │(BM25+语义)   │  │ (Provider映射)│  │ (SQLite)     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
        │               │                   │
        ▼               ▼                   ▼
┌─────────────────────────────────────────────────────────────┐
│                      存储层                                  │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌───────────────┐             │
│  │ FAISS    │  │ Ollama   │  │ SQLite         │             │
│  │ (向量)   │  │ (本地嵌入)│  │ (auth/对话)    │             │
│  └──────────┘  └──────────┘  └───────────────┘             │
│   vector_store/   localhost:11434   data/                   │
└─────────────────────────────────────────────────────────────┘
```

## RAG 系统详解

RAG 是系统最核心的模块，由 `RAGSystem` 统一编排，内部组合了多个子系统。

### 文档处理流水线

```
源文档 (.md/.pdf/.txt/.docx)
        │
        ▼
  DocumentLoader.load_document()
        │  按格式选择加载器，提取元数据
        ▼
  TextSplitter.split_documents()
        │  chunk_size=1000, overlap=200
        │  策略：recursive（按 \n\n → \n → 。断句）
        ▼
  OllamaEmbeddings (nomic-embed-text)
        │  本地向量化，1536 维
        ▼
  FAISS.from_documents()
        │  构建 HNSW 向量索引
        ▼
  BM25.fit(documents)
        │  训练关键词索引
        ▼
  存储到 vector_store/
  ├── index.faiss    (向量索引)
  └── index.pkl      (文档元数据)
```

### 混合检索 (retrieve_hybrid)

```python
def retrieve_hybrid(query: str, k: int = 5, bm25_weight: float = 0.3):
    # 1. 语义搜索：FAISS 余弦相似度 → Top K
    semantic_docs = vector_store.similarity_search(query, k=k*2)

    # 2. 关键词搜索：BM25 分词匹配 → Top K
    bm25_docs = bm25.search(query, k=k*2)

    # 3. 加权融合：score = bm25_weight * bm25_score + (1-bm25_weight) * semantic_score
    merged = weighted_fusion(semantic_docs, bm25_docs, alpha=bm25_weight)

    return merged[:k]
```

**BM25 权重 0.3 的含义**：30% 看重精确关键词匹配（适合产品名、术语），70% 看重语义相似度（适合概念性查询）。对"红利策略"这种查询，BM25 能精确命中含"红利"的文档，语义部分找到投资策略相关内容。

### 检索到生成

```python
# 用户查询
query = "当前应该加仓还是减仓红利产品"

# Step 1: 混合检索
docs = rag.retrieve_hybrid(query, k=3)  # 返回 3 篇最相关文档

# Step 2: 构建 prompt
prompt = RAGPromptBuilder.build_qa(
    query=query,
    contexts=[d.page_content for d in docs],
    max_context_length=4000,
)

# Step 3: LLM 生成
answer = llm.generate(prompt)
```

### 高级检索能力

| 方法 | 功能 |
|------|------|
| `retrieve_documents()` | 纯语义搜索 |
| `retrieve_hybrid()` | BM25+语义混合搜索 |
| `search_by_metadata()` | 元数据过滤 + 语义搜索 |
| `search_by_name()` | 按文档名精确搜索 |
| `search_by_category()` | 按分类（如 investment/persona）过滤 |
| `rerank_documents()` | LLM 对检索结果重排序 |

## 多模型支持

### 模型解析流程

```
用户指定模型名 (如 "deepseek-chat")
        │
        ▼
  _resolve_provider(model_name)
        │
        ├── 含 "/" ? → Ollama 本地模型 (如 "ollama/gemma3")
        │
        └── 不含 "/" ? → 查 PROVIDER_MAP
                │
                ├── "deepseek-" → provider="deepseek", model="deepseek/deepseek-chat"
                ├── "claude-"   → provider="anthropic"
                ├── "gemini-"   → provider="google"
                ├── "gpt-"      → provider="openai"
                └── 其他       → provider=None (LiteLLM 自动推断)
```

### 支持的模型

| 类别 | 模型 | 方式 |
|------|------|------|
| 本地 | gemma3, llama3, deepseek-r1, qwen3-coder | Ollama (localhost:11434) |
| 云端 | deepseek-chat, deepseek-reasoner | DeepSeek API |
| 云端 | gpt-4o, gpt-4o-mini | OpenAI API |
| 云端 | claude-sonnet-4-6, claude-opus-4-7 | Anthropic API |
| 云端 | gemini-3.1-pro | Google API |

### LLMIntegration 调用层

```python
class LLMIntegration:
    def generate(self, prompt: str) -> str:
        # 带重试（max_retries=3）、缓存（TTL=2h）、速率限制
        if cached := self.cache.get(prompt):
            return cached
        self.rate_limiter.acquire()
        result = self._generate_ollama(prompt)  # 或 _generate_litellm()
        self.cache.set(prompt, result)
        return result
```

## 认证系统

### 三层认证

```
请求到达 API
    │
    ├── 1. INTERNAL_API_KEY 环境变量 ?
    │       └── 匹配 → 内部用户，scopes=["*"]
    │
    ├── 2. Authorization: Bearer <jwt> ?
    │       └── 验证成功 → 从 payload 提取 user_id + scopes
    │
    └── 3. X-API-Key: lk-<random> ?
            └── SHA256 匹配 → 查找对应用户
```

### 认证存储

```
data/auth.db (SQLite)
├── users       (id, username, password_hash, created_at)
├── api_keys    (id, user_id, key_hash, name, scopes, last_used, created_at)
└── tokens      (id, user_id, token_hash, expires_at, created_at)
```

密码使用 PBKDF2-HMAC-SHA256（10万次迭代），API Key 使用 SHA256 哈希存储。

## 配置

```bash
# .env
# === API Keys ===
OPENAI_API_KEY=sk-xxx
ANTHROPIC_API_KEY=sk-ant-xxx
GOOGLE_API_KEY=xxx

# === Ollama ===
OLLAMA_BASE_URL=http://localhost:11434

# === 默认模型 ===
DEFAULT_MODEL=deepseek-chat
DEFAULT_TEMPERATURE=0.7

# === RAG ===
VECTOR_STORE_TYPE=faiss          # faiss 或 qdrant
RAG_FAISS_PATH=./vector_store
RAG_COLLECTION_NAME=langchain_documents

# === 应用 ===
DEBUG=false
INTERNAL_API_KEY=xxx             # 内部 API Key，拥有全部权限
```

## CLI 命令

```bash
# 文本生成
langchain-cli generate "用中文解释什么是 ETF"

# 交互式聊天
langchain-cli chat
# > 今天推荐什么投资策略？
# > exit

# 模型管理
langchain-cli model list          # 列出所有模型
langchain-cli model set deepseek-reasoner

# 温度调节
langchain-cli temperature set 0.3
langchain-cli temperature get
```

## REST API

**启动**：`langchain-cli api`（默认 `http://localhost:8000`）  
**接口文档**：`http://localhost:8000/docs`（Swagger UI）

### 核心端点

```
POST /api/v1/generate             文本生成 (需认证)
POST /api/v1/chat                 对话模式 (需认证)

POST /api/v1/rag/query            RAG 查询
POST /api/v1/rag/hybrid           混合 RAG (BM25+语义)
POST /api/v1/rag/upload           上传文档
POST /api/v1/rag/import-directory 批量导入目录
GET  /api/v1/rag/info             向量库信息

POST /api/v1/auth/register        注册
POST /api/v1/auth/login           登录 (返回 JWT)
POST /api/v1/auth/api-keys        创建 API Key

GET  /api/v1/models               列出所有模型
GET  /api/v1/cost/report          成本报告
GET  /api/v1/performance/stats    性能统计
```

完整端点列表见 Swagger 文档。

## Web UI

**启动**：

```bash
# 完整 Web UI（Streamlit，默认 8501）
streamlit run src/langchain_llm_toolkit/app.py

# 轻量知识库查询页（无需 Streamlit，默认 8502）
python rag_query_web.py 8502
```

5 个页面（Streamlit 版）：
- **智能对话**：标准聊天界面，支持流式输出
- **RAG 问答**：上传文档后提问，显示参考来源
- **对话管理**：保存/加载/导出对话历史
- **文档管理**：批量上传、查看、清空向量库
- **账户设置**：登录注册、API Key 管理

所有页面共享侧边栏的模型选择和温度配置。

## 设计决策

### 为什么本地嵌入？

Ollama 本地运行 `nomic-embed-text` 做文档向量化，不调用外部嵌入 API。所有知识文档和向量索引完全存储在本地磁盘，保护隐私。

### 为什么 BM25 + 语义混合？

纯语义搜索对产品名、术语等关键词不敏感。BM25 补上了精确匹配的能力。30% 权重在 60+ 篇文档的库中已能有效提升精确度，更大规模时优势更明显。

### 为什么 LiteLLM？

统一接口接入 5+ 个模型提供商，切换模型只需改一个字符串。成本追踪、速率限制等功能开箱即用。

### 为什么三种入口？

- **CLI**：开发和调试时快速测试
- **API**：程序化集成，给 autogen-asset-analyst 等下游系统提供知识检索
- **Web UI**：非技术人员也能浏览知识库、上传文档

## 项目结构

```
langchain-llm-toolkit/
├── src/langchain_llm_toolkit/
│   ├── rag.py                  # RAG 核心（索引、检索、生成、混合搜索）
│   ├── hybrid_retriever.py     # BM25 + HybridRetriever + HybridRAGSystem
│   ├── document_loader.py      # 多格式文档加载（PDF/TXT/MD/DOCX）
│   ├── text_splitter.py        # 文档分块（recursive/character/markdown/semantic）
│   ├── llm_integration.py      # LLM 调用层（Ollama + LiteLLM）
│   ├── api.py                  # FastAPI 应用（25 个端点）
│   ├── app.py                  # Streamlit Web UI（5 页）
│   ├── auth.py                 # 认证系统（JWT + API Key + SQLite）
│   ├── cli.py                  # Typer 命令行
│   ├── config/settings.py      # Pydantic 配置
│   ├── models/schemas.py       # API 数据模型
│   ├── prompt_templates.py     # 提示模板
│   ├── conversation.py         # 内存对话管理
│   ├── conversation_store.py   # SQLite 持久化
│   ├── cache.py                # 缓存管理
│   ├── performance.py          # 性能监控（LRU缓存、并行处理）
│   ├── rate_limiter.py         # 速率限制（固定窗口/令牌桶/多层级）
│   ├── token_cost_manager.py   # Token 计数 + 成本估算
│   ├── evaluate_rag.py         # RAG 评估
│   ├── import_docs.py          # 文档批量导入
│   ├── document_import_manager.py # 导入管理器
│   ├── markdown_loader.py      # 增强版 Markdown 加载
│   ├── metadata_generator.py   # 元数据生成
│   ├── exceptions.py           # 异常体系
│   ├── logger.py               # 日志配置
│   └── agent/                  # Agent 子系统
│       ├── base.py             # Agent 基类
│       ├── react_agent.py      # ReAct Agent
│       ├── task_planner.py     # 任务规划器
│       ├── tools.py            # 工具系统
│       └── builtin_tools.py    # 内置工具（计算器/搜索/文件/Python等）
├── tests/                      # 643 测试，64% 覆盖率
├── vector_store/               # FAISS 向量库
├── data/                       # SQLite 数据库
├── .env
├── pyproject.toml
├── README.md
├── README.zh-CN.md
└── docs/
    └── architecture.md         # 本文档
```
