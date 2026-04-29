import json
import time
import tempfile
import os

from fastapi import FastAPI, HTTPException, UploadFile, File, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi import status

from langchain_llm_toolkit.models.schemas import (
    GenerateRequest,
    GenerateResponse,
    ChatRequest,
    ChatResponse,
    RAGQueryRequest,
    RAGQueryResponse,
    RAGUploadResponse,
    SourceDocument,
    ModelsResponse,
    ModelInfo,
    HealthResponse,
)
from langchain_llm_toolkit.llm_integration import LLMIntegration
from langchain_llm_toolkit.rag import RAGSystem
from langchain_llm_toolkit.hybrid_retriever import HybridRAGSystem
from langchain_llm_toolkit.conversation_store import ConversationStore
from langchain_llm_toolkit.auth import AuthManager, get_current_user, TokenData
from langchain_llm_toolkit.logger import logger
from langchain_llm_toolkit.exceptions import (
    LLMToolkitError,
    APIKeyMissingError,
    APIConnectionError,
    APITimeoutError,
    RateLimitExceededError,
)
from langchain_llm_toolkit.rate_limiter import RateLimiter

app = FastAPI(
    title="LangChain LLM Toolkit API",
    description="基于 LangChain 和 LiteLLM 的完整 LLM 工具集 API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

rate_limiter = RateLimiter(max_requests=100, window_seconds=60)


@app.exception_handler(LLMToolkitError)
async def llm_toolkit_exception_handler(request: Request, exc: LLMToolkitError):
    logger.error(f"LLM Toolkit error: {exc}")
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    if isinstance(exc, APIKeyMissingError):
        status_code = status.HTTP_401_UNAUTHORIZED
    elif isinstance(exc, RateLimitExceededError):
        status_code = status.HTTP_429_TOO_MANY_REQUESTS
    elif isinstance(exc, (APIConnectionError, APITimeoutError)):
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        status_code=status_code,
        content={
            "error": exc.message,
            "details": exc.details,
            "type": type(exc).__name__,
        },
    )


rag_system_instance = None
hybrid_rag_instance = None
conversation_store = None
auth_manager = None


def get_rag_system():
    global rag_system_instance
    if rag_system_instance is None:
        rag_system_instance = RAGSystem()
    return rag_system_instance


def get_hybrid_rag():
    global hybrid_rag_instance
    if hybrid_rag_instance is None:
        rag = get_rag_system()
        hybrid_rag_instance = HybridRAGSystem(rag)
    return hybrid_rag_instance


def get_conversation_store():
    global conversation_store
    if conversation_store is None:
        conversation_store = ConversationStore()
    return conversation_store


def get_auth_manager():
    global auth_manager
    if auth_manager is None:
        auth_manager = AuthManager()
    return auth_manager


@app.get("/", response_model=HealthResponse, tags=["Root"])
async def root():
    return HealthResponse(status="healthy", version="1.0.0")


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    return HealthResponse(status="healthy", version="1.0.0")


@app.post("/api/v1/generate", response_model=GenerateResponse, tags=["Generation"])
async def generate_text(request: GenerateRequest, req: Request):
    client_ip = req.client.host if req.client else "unknown"
    try:
        rate_limiter.check_rate_limit(f"generate:{client_ip}")
    except RateLimitExceededError as e:
        logger.warning(f"Rate limit exceeded for {client_ip}: {e}")
        raise

    start_time = time.time()

    try:
        logger.info(f"Generate request - model: {request.model}, prompt: {request.prompt[:50]}...")

        llm = LLMIntegration(timeout=request.timeout)
        llm.set_model(request.model)
        llm.set_temperature(request.temperature)

        response = llm.generate(request.prompt)

        elapsed_time = time.time() - start_time
        logger.info(f"Generate completed in {elapsed_time:.2f}s")

        return GenerateResponse(response=response, model=request.model, elapsed_time=elapsed_time)

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating text: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.post("/api/v1/generate/stream", tags=["Generation"])
async def generate_text_stream(request: GenerateRequest):
    if not request.model.startswith("ollama/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Streaming only supported for Ollama models "
                "(model name must start with 'ollama/')"
            ),
        )

    async def generate():
        try:
            llm = LLMIntegration(timeout=request.timeout)
            llm.set_model(request.model)
            llm.set_temperature(request.temperature)

            for chunk in llm.generate_stream(request.prompt):
                yield f"data: {json.dumps({'content': chunk})}\n\n"

            yield f"data: {json.dumps({'done': True})}\n\n"

        except Exception as e:
            logger.error(f"Error in stream generation: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.post("/api/v1/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(request: ChatRequest):
    start_time = time.time()

    try:
        logger.info(f"Chat request - model: {request.model}, messages: {len(request.messages)}")

        llm = LLMIntegration(timeout=request.timeout)
        llm.set_model(request.model)
        llm.set_temperature(request.temperature)

        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        response = llm.chat(messages)

        elapsed_time = time.time() - start_time
        logger.info(f"Chat completed in {elapsed_time:.2f}s")

        return ChatResponse(response=response, model=request.model, elapsed_time=elapsed_time)

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.post("/api/v1/chat/stream", tags=["Chat"])
async def chat_stream(request: ChatRequest):
    if not request.model.startswith("ollama/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Streaming only supported for Ollama models",
        )

    async def generate():
        try:
            llm = LLMIntegration(timeout=request.timeout)
            llm.set_model(request.model)
            llm.set_temperature(request.temperature)

            messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]

            for chunk in llm.chat_stream(messages):
                yield f"data: {json.dumps({'content': chunk})}\n\n"

            yield f"data: {json.dumps({'done': True})}\n\n"

        except Exception as e:
            logger.error(f"Error in chat stream: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.post("/api/v1/rag/query", response_model=RAGQueryResponse, tags=["RAG"])
async def rag_query(request: RAGQueryRequest):
    try:
        logger.info(f"RAG query: {request.query[:50]}...")

        rag_system = get_rag_system()

        try:
            rag_system.load_vector_store("vector_store")
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vector store not found. Please upload documents first.",
            )

        answer, relevant_docs = rag_system.generate_answer(request.query, k=request.k)

        sources = [
            SourceDocument(content=doc.page_content, metadata=doc.metadata) for doc in relevant_docs
        ]

        logger.info(f"RAG query completed, found {len(sources)} sources")

        return RAGQueryResponse(answer=answer, sources=sources)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in RAG query: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.post("/api/v1/rag/query/stream", tags=["RAG"])
async def rag_query_stream(request: RAGQueryRequest):
    async def generate():
        try:
            rag_system = get_rag_system()
            rag_system.load_vector_store("vector_store")

            relevant_docs = rag_system.retrieve_documents(request.query, k=request.k)

            sources_data = [
                {
                    "content": (
                        doc.page_content[:200] + "..."
                        if len(doc.page_content) > 200
                        else doc.page_content
                    ),
                    "source": doc.metadata.get("source", "unknown"),
                }
                for doc in relevant_docs
            ]
            yield f"data: {json.dumps({'sources': sources_data})}\n\n"

            answer, _ = rag_system.generate_answer(request.query, k=request.k)

            for i in range(0, len(answer), 20):
                chunk = answer[i : i + 20]
                yield f"data: {json.dumps({'content': chunk})}\n\n"

            yield f"data: {json.dumps({'done': True})}\n\n"

        except Exception as e:
            logger.error(f"Error in RAG stream: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.post("/api/v1/rag/hybrid", tags=["RAG"])
async def rag_hybrid_query(request: RAGQueryRequest, alpha: float = 0.3):
    try:
        logger.info(f"Hybrid RAG query: {request.query[:50]}..., alpha={alpha}")

        hybrid_rag = get_hybrid_rag()
        hybrid_rag.rag.load_vector_store("vector_store")

        answer, relevant_docs = hybrid_rag.generate_answer(request.query, k=request.k, alpha=alpha)

        sources = [
            SourceDocument(content=doc.page_content, metadata=doc.metadata) for doc in relevant_docs
        ]

        return RAGQueryResponse(answer=answer, sources=sources)

    except Exception as e:
        logger.error(f"Error in hybrid RAG query: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.post("/api/v1/rag/upload", response_model=RAGUploadResponse, tags=["RAG"])
async def rag_upload(file: UploadFile = File(...)):
    try:
        logger.info(f"Uploading file: {file.filename}")

        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Filename is required"
            )

        allowed_extensions = [".pdf", ".txt", ".docx", ".md"]
        file_ext = os.path.splitext(file.filename)[1].lower()

        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not supported. Allowed: {', '.join(allowed_extensions)}",
            )

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_ext)
        content = await file.read()
        temp_file.write(content)
        temp_file.close()

        rag_system = get_rag_system()
        documents = rag_system.load_and_process_documents([temp_file.name])
        rag_system.create_vector_store(documents)
        rag_system.save_vector_store("vector_store")

        os.unlink(temp_file.name)

        logger.info(f"File processed successfully: {file.filename}")

        return RAGUploadResponse(
            message="File processed successfully",
            filename=file.filename or "unknown",
            documents_count=len(documents),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/api/v1/models", response_model=ModelsResponse, tags=["Models"])
async def list_models():
    models = [
        ModelInfo(name="ollama/gemma4", type="local", description="Ollama - gemma4 模型（本地运行，推荐）"),
        ModelInfo(name="ollama/gemma3", type="local", description="Ollama - gemma3 模型（本地运行）"),
        ModelInfo(
            name="ollama/llama3.1:8b", type="local", description="Ollama - llama3.1 8B 模型（本地运行）"
        ),
        ModelInfo(
            name="ollama/deepseek-r1:7b",
            type="local",
            description="Ollama - deepseek-r1 7B 模型（本地运行）",
        ),
        ModelInfo(
            name="ollama/deepseek-v3",
            type="local",
            description="Ollama - deepseek-v3 模型（本地运行）",
        ),
        ModelInfo(name="gpt-5.3", type="cloud", description="OpenAI - GPT-5.3 模型（最新，需要 API Key）"),
        ModelInfo(name="gpt-4o", type="cloud", description="OpenAI - GPT-4o 模型（需要 API Key）"),
        ModelInfo(
            name="gpt-3.5-turbo", type="cloud", description="OpenAI - GPT-3.5 Turbo 模型（需要 API Key）"
        ),
        ModelInfo(
            name="deepseek-chat",
            type="cloud",
            description="DeepSeek - V4 模型（最新，需要 API Key）",
        ),
        ModelInfo(
            name="deepseek-reasoner",
            type="cloud",
            description="DeepSeek - R1 推理模型（需要 API Key）",
        ),
        ModelInfo(
            name="claude-3-opus",
            type="cloud",
            description="Anthropic - Claude 3 Opus 模型（需要 API Key）",
        ),
    ]
    return ModelsResponse(models=models)


@app.get("/api/v1/performance/stats", tags=["Performance"])
async def get_performance_stats():
    """获取性能统计信息"""
    from langchain_llm_toolkit.performance import query_cache, performance_monitor

    return {
        "cache": query_cache.get_stats(),
        "metrics": performance_monitor.get_all_stats(),
    }


@app.get("/api/v1/performance/cache", tags=["Performance"])
async def get_cache_stats():
    """获取缓存统计信息"""
    from langchain_llm_toolkit.performance import query_cache

    return query_cache.get_stats()


@app.delete("/api/v1/performance/cache", tags=["Performance"])
async def clear_cache():
    """清空缓存"""
    from langchain_llm_toolkit.performance import query_cache

    query_cache.cache.clear()
    return {"message": "Cache cleared successfully"}


@app.get("/api/v1/rag/info", tags=["RAG"])
async def rag_info():
    try:
        rag_system = get_rag_system()
        try:
            info = rag_system.get_collection_info()
            return {
                "status": "ready",
                "vector_store_type": rag_system.vector_store_type,
                "collection_info": info,
            }
        except Exception:
            return {
                "status": "not_initialized",
                "vector_store_type": rag_system.vector_store_type,
                "message": "Vector store not initialized. Please upload documents first.",
            }
    except Exception as e:
        logger.error(f"Error getting RAG info: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.delete("/api/v1/rag/clear", tags=["RAG"])
async def rag_clear():
    try:
        rag_system = get_rag_system()
        rag_system.delete_collection()

        global rag_system_instance, hybrid_rag_instance
        rag_system_instance = None
        hybrid_rag_instance = None

        logger.info("RAG vector store cleared")
        return {"message": "Vector store cleared successfully"}

    except Exception as e:
        logger.error(f"Error clearing RAG: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.post("/api/v1/conversations", tags=["Conversations"])
async def create_conversation(title: str = "新对话"):
    try:
        store = get_conversation_store()
        import uuid
        from datetime import datetime
        from langchain_llm_toolkit.conversation_store import Conversation

        now = datetime.now().isoformat()
        conversation = Conversation(
            id=str(uuid.uuid4()),
            title=title,
            messages=[],
            created_at=now,
            updated_at=now,
        )
        store.save_conversation(conversation)
        return conversation.to_dict()
    except Exception as e:
        logger.error(f"Error creating conversation: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/api/v1/conversations", tags=["Conversations"])
async def list_conversations(limit: int = 20, offset: int = 0):
    try:
        store = get_conversation_store()
        conversations = store.list_conversations(limit=limit, offset=offset)
        return {"conversations": [c.to_dict() for c in conversations]}
    except Exception as e:
        logger.error(f"Error listing conversations: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/api/v1/conversations/stats", tags=["Conversations"])
async def conversation_stats():
    try:
        store = get_conversation_store()
        return store.get_stats()
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/api/v1/conversations/{conversation_id}", tags=["Conversations"])
async def get_conversation(conversation_id: str):
    try:
        store = get_conversation_store()
        conversation = store.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
            )
        return conversation.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.delete("/api/v1/conversations/{conversation_id}", tags=["Conversations"])
async def delete_conversation(conversation_id: str):
    try:
        store = get_conversation_store()
        store.delete_conversation(conversation_id)
        return {"message": "Conversation deleted"}
    except Exception as e:
        logger.error(f"Error deleting conversation: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.post("/api/v1/auth/register", tags=["Auth"])
async def register(username: str, email: str, password: str):
    try:
        manager = get_auth_manager()
        user = manager.create_user(username, email, password)
        return {"message": "User created", "user_id": user.id, "username": user.username}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.post("/api/v1/auth/login", tags=["Auth"])
async def login(username: str, password: str):
    try:
        manager = get_auth_manager()
        user = manager.authenticate_user(username, password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
            )

        token = manager.create_access_token(user)
        return {"access_token": token, "token_type": "bearer", "user_id": user.id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error logging in: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.post("/api/v1/auth/api-keys", tags=["Auth"])
async def create_api_key(name: str, current_user: TokenData = Depends(get_current_user)):
    try:
        manager = get_auth_manager()
        api_key = manager.create_api_key(current_user.user_id, name)
        return {"api_key": api_key, "name": name}
    except Exception as e:
        logger.error(f"Error creating API key: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/api/v1/auth/api-keys", tags=["Auth"])
async def list_api_keys(current_user: TokenData = Depends(get_current_user)):
    try:
        manager = get_auth_manager()
        keys = manager.store.list_api_keys(current_user.user_id)
        return {"api_keys": keys}
    except Exception as e:
        logger.error(f"Error listing API keys: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.delete("/api/v1/auth/api-keys/{key_id}", tags=["Auth"])
async def revoke_api_key(key_id: str, current_user: TokenData = Depends(get_current_user)):
    try:
        manager = get_auth_manager()
        manager.store.revoke_api_key(key_id)
        return {"message": "API key revoked"}
    except Exception as e:
        logger.error(f"Error revoking API key: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/api/v1/auth/me", tags=["Auth"])
async def get_current_user_info(current_user: TokenData = Depends(get_current_user)):
    return {
        "user_id": current_user.user_id,
        "username": current_user.username,
        "scopes": current_user.scopes,
    }


def run_server(host: str = "127.0.0.1", port: int = 8000):
    import argparse
    import uvicorn

    parser = argparse.ArgumentParser(description="启动 LangChain LLM Toolkit API 服务器")
    parser.add_argument("--host", type=str, default=host, help="服务器地址 (默认: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=port, help="服务器端口 (默认: 8000)")
    args = parser.parse_args()

    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    run_server()
