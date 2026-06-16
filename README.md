<div align="right">
  <a href="README.zh-CN.md">🇨🇳 中文</a>
</div>

# LangChain LLM Toolkit

A complete LLM toolkit built on LangChain and LiteLLM, supporting text generation, chat, and RAG document Q&A.

## Features

- **Multi-Model Integration**: Use LiteLLM to call various AI models (OpenAI, Anthropic, Google, Ollama, etc.)
- **Text Generation**: Basic text generation and chat mode with streaming support
- **RAG System**: Retrieval-Augmented Generation with hybrid search (BM25 + semantic retrieval)
- **Document Processing**: Load and process documents in multiple formats (PDF, TXT, DOCX, Markdown)
- **Vector Storage**: Support for Qdrant and FAISS vector databases
- **Conversation Persistence**: SQLite-based conversation history storage
- **API Authentication**: JWT and API Key authentication
- **Streaming Response**: SSE streaming API responses
- **Performance Optimization**: LRU cache, query cache, parallel processing

## Project Structure

```
langchain-llm-toolkit/
├── src/langchain_llm_toolkit/    # Source code
│   ├── agent/                    # Agent system
│   │   ├── base.py              # Base agent class
│   │   ├── react_agent.py       # ReAct agent implementation
│   │   ├── task_planner.py      # Task planning & decomposition
│   │   ├── tools.py             # Agent tool definitions
│   │   └── builtin_tools.py     # Built-in tool implementations
│   ├── models/                   # Data models
│   │   └── schemas.py           # Pydantic request/response schemas
│   ├── config/                   # Configuration management
│   │   └── settings.py          # Pydantic settings (.env based)
│   ├── api.py                    # FastAPI REST API service
│   ├── app.py                    # Streamlit Web UI
│   ├── cli.py                    # Command-line interface
│   ├── rag.py                    # RAG system core
│   ├── hybrid_retriever.py       # Hybrid retriever (BM25 + vector)
│   ├── llm_integration.py        # LLM integration via LiteLLM
│   ├── conversation_store.py     # SQLite-based conversation persistence
│   ├── conversation.py           # Conversation data models
│   ├── auth.py                   # JWT / API Key authentication
│   ├── cache.py                  # LRU + query cache system
│   ├── performance.py            # Performance monitoring & optimization
│   ├── rate_limiter.py           # API rate limiting
│   ├── token_cost_manager.py     # LLM token cost tracking
│   ├── prompt_templates.py       # System prompt templates
│   ├── text_splitter.py          # Document chunking strategies
│   ├── document_loader.py        # Multi-format document loader
│   ├── markdown_loader.py        # Markdown-specific loader
│   ├── metadata_generator.py     # Document metadata extraction
│   ├── document_import_manager.py # Document import orchestration
│   ├── import_docs.py            # Document import CLI commands
│   ├── evaluate_rag.py           # RAG quality evaluation metrics
│   ├── exceptions.py             # Custom exception hierarchy
│   ├── logger.py                 # Structured logging
│   └── __init__.py               # Package init
├── tests/                        # Test suite (30+ test files)
├── docs/                         # Documentation
│   ├── Agent.md                  # Agent system guide
│   ├── Claude.md                 # Claude integration notes
│   ├── Skill.md                  # Skill definitions
│   ├── AI_VS_RAG_COMPARISON.md   # AI vs RAG comparison
│   ├── CHANGELOG.md              # Version history
│   ├── CONTRIBUTING.md           # Contribution guidelines
│   ├── SECURITY_AUDIT.md         # Security audit report
│   └── SECURITY.md               # Security policy
├── examples/                     # Usage examples
│   └── agent_example.py          # Agent usage demo
├── pyproject.toml                # Project config (uv/pip)
├── Makefile                      # Build & dev commands
├── pytest.ini                    # pytest configuration
├── render.yaml                   # Render deployment config
├── .env.example                  # Environment template
├── .pre-commit-config.yaml       # Pre-commit hooks
└── LICENSE                      # MIT License
```

## Quick Start

### Installation

```bash
# Clone the project
git clone <repository-url>
cd langchain-llm-toolkit

# Install dependencies (using uv)
make install

# Or use pip
pip install -e .
```

### Environment Configuration

Create a `.env` file:

```env
# API Keys (optional, not needed when using Ollama local models)
OPENAI_API_KEY=your_openai_api_key

# Ollama settings
OLLAMA_BASE_URL=http://localhost:11434

# Model settings
DEFAULT_MODEL=ollama/gemma4
EMBEDDING_MODEL=snowflake-arctic-embed2
```

### Using Ollama Local Models

```bash
# Install Ollama
brew install ollama  # macOS
# Or visit https://ollama.com to download

# Pull models
ollama pull gemma4                    # LLM model
ollama pull snowflake-arctic-embed2   # Embedding model

# Start service
ollama serve
```

## Usage

### 1. Command Line Interface

```bash
# Text generation
langchain-cli generate "Hello, please introduce yourself" --model ollama/gemma4

# Chat mode
langchain-cli chat --model ollama/gemma4

# Import documents to RAG knowledge base
langchain-import ./docs '*.md'
```

### 2. Web UI (Streamlit)

```bash
# Launch Web interface
langchain-cli web
# or
make web
```

Visit http://localhost:8501 to use the Web interface.

### 3. API Service

```bash
# Start API service
langchain-api
# or
make api
```

API documentation: http://localhost:8000/docs

### 4. Python API

```python
from langchain_llm_toolkit.llm_integration import LLMIntegration
from langchain_llm_toolkit.rag import RAGSystem

# LLM usage
llm = LLMIntegration(model="ollama/gemma4")
response = llm.generate("Hello")
print(response)

# Streaming output
for chunk in llm.generate_stream("Tell me a story"):
    print(chunk, end="", flush=True)

# RAG system
rag = RAGSystem()
rag.load_vector_store()
answer, docs = rag.generate_answer("What is LangChain?")
print(answer)
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/generate` | POST | Text generation |
| `/api/v1/chat` | POST | Chat conversation |
| `/api/v1/generate/stream` | POST | Streaming generation |
| `/api/v1/rag/query` | POST | RAG query |
| `/api/v1/rag/upload` | POST | Upload document |
| `/api/v1/models` | GET | Get model list |
| `/api/v1/conversations` | GET | Get conversation list |
| `/api/v1/auth/login` | POST | User login |

## Recommended Models

### LLM Models

#### Local Models (Ollama)

| Model | Size | Description |
|-------|------|-------------|
| gemma4 | 9.6 GB | Recommended, good performance |
| llama3.1:8b | 4.7 GB | Balanced choice |
| deepseek-r1:7b | 4.7 GB | Strong reasoning |

#### Cloud Models

| Model | Description |
|-------|-------------|
| gpt-5.3 | OpenAI latest model, requires API Key |
| gpt-4o | OpenAI multimodal model |
| deepseek-chat | DeepSeek V4 latest model, requires API Key |
| deepseek-reasoner | DeepSeek R1 reasoning model, requires API Key |
| claude-opus-4-7 | Anthropic latest model |

### Embedding Models

| Model | Size | Context | Dimensions | Description |
|-------|------|---------|------------|-------------|
| snowflake-arctic-embed2 | 1.2 GB | 8192 | 1024 | Recommended, multilingual |
| nomic-embed-text | 274 MB | 8192 | 768 | Lightweight option |

## Development

### Running Tests

```bash
# Run all tests
make test

# Run tests with coverage report
make test-coverage
```

### Code Quality

```bash
# Format code
make format

# Lint code
make lint
```

### Makefile Commands

```bash
make help          # Show all commands
make install       # Install dependencies
make test          # Run tests
make format        # Format code
make lint          # Lint code
make web           # Start Web UI
make api           # Start API service
make clean         # Clean caches
```

## Test Coverage

Current test coverage: **38%**

| Module | Coverage |
|--------|----------|
| api.py | 69% |
| llm_integration.py | 72% |
| rag.py | 55% |
| cache.py | 64% |
| performance.py | 64% |

## License

MIT License - See [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](docs/CONTRIBUTING.md) for details.
