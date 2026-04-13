from fastapi import FastAPI, HTTPException, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi import status
import time
import tempfile
import os

from models.schemas import (
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
from llm_integration import LLMIntegration
from rag import RAGSystem
from logger import logger
from exceptions import (
    LLMToolkitError,
    APIKeyMissingError,
    APIConnectionError,
    APITimeoutError,
    RateLimitExceededError,
)
from rate_limiter import RateLimiter

# 创建 FastAPI 应用
app = FastAPI(
    title="LangChain LLM Toolkit API",
    description="基于 LangChain 和 LiteLLM 的完整 LLM 工具集 API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局速率限制器
rate_limiter = RateLimiter(max_requests=100, window_seconds=60)


@app.exception_handler(LLMToolkitError)
async def llm_toolkit_exception_handler(request: Request, exc: LLMToolkitError):
    """自定义异常处理器"""
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


# 全局变量
rag_system_instance = None


def get_rag_system():
    """获取 RAG 系统实例"""
    global rag_system_instance
    if rag_system_instance is None:
        rag_system_instance = RAGSystem()
    return rag_system_instance


# 根路径
@app.get("/", response_model=HealthResponse, tags=["Root"])
async def root():
    """根路径 - 健康检查"""
    return HealthResponse(status="healthy", version="1.0.0")


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """健康检查端点"""
    return HealthResponse(status="healthy", version="1.0.0")


# 文本生成端点
@app.post("/api/v1/generate", response_model=GenerateResponse, tags=["Generation"])
async def generate_text(request: GenerateRequest, req: Request):
    """
    生成文本

    - **prompt**: 输入提示（必填）
    - **model**: 模型名称（默认: ollama/gemma3）
    - **temperature**: 温度参数（默认: 0.7）
    - **timeout**: 超时时间（默认: 30秒）
    """
    # 检查速率限制
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


# 流式生成端点
@app.post("/api/v1/generate/stream", tags=["Generation"])
async def generate_text_stream(request: GenerateRequest):
    """
    流式生成文本（仅支持 Ollama 模型）

    - **prompt**: 输入提示（必填）
    - **model**: 模型名称（必须以 ollama/ 开头）
    - **temperature**: 温度参数（默认: 0.7）
    """
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
                yield f"data: {chunk}\n\n"

            yield "data: [DONE]\n\n"

        except Exception as e:
            logger.error(f"Error in stream generation: {e}")
            yield f"data: Error: {str(e)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


# 聊天端点
@app.post("/api/v1/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(request: ChatRequest):
    """
    聊天模式

    - **messages**: 消息列表（必填）
    - **model**: 模型名称（默认: ollama/gemma3）
    - **temperature**: 温度参数（默认: 0.7）
    - **timeout**: 超时时间（默认: 30秒）
    """
    start_time = time.time()

    try:
        logger.info(f"Chat request - model: {request.model}, messages: {len(request.messages)}")

        llm = LLMIntegration(timeout=request.timeout)
        llm.set_model(request.model)
        llm.set_temperature(request.temperature)

        # 转换消息格式
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


# RAG 查询端点
@app.post("/api/v1/rag/query", response_model=RAGQueryResponse, tags=["RAG"])
async def rag_query(request: RAGQueryRequest):
    """
    RAG 查询

    - **query**: 查询内容（必填）
    - **k**: 返回的相关文档数量（默认: 3）
    """
    try:
        logger.info(f"RAG query: {request.query[:50]}...")

        rag_system = get_rag_system()

        # 尝试加载向量存储
        try:
            rag_system.load_vector_store("vector_store")
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vector store not found. Please upload documents first.",
            )

        # 生成回答
        answer, relevant_docs = rag_system.generate_answer(request.query, k=request.k)

        # 转换文档格式
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


# RAG 文档上传端点
@app.post("/api/v1/rag/upload", response_model=RAGUploadResponse, tags=["RAG"])
async def rag_upload(file: UploadFile = File(...)):
    """
    上传文档到 RAG 系统

    - **file**: 文档文件（支持 PDF, TXT, DOCX）
    """
    try:
        logger.info(f"Uploading file: {file.filename}")

        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename is required",
            )

        # 检查文件类型
        allowed_extensions = [".pdf", ".txt", ".docx"]
        file_ext = os.path.splitext(file.filename)[1].lower()

        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not supported. Allowed: {', '.join(allowed_extensions)}",
            )

        # 保存上传的文件
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_ext)
        content = await file.read()
        temp_file.write(content)
        temp_file.close()

        # 处理文档
        rag_system = get_rag_system()
        documents = rag_system.load_and_process_documents([temp_file.name])
        rag_system.create_vector_store(documents)
        rag_system.save_vector_store("vector_store")

        # 清理临时文件
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


# 获取支持的模型列表
@app.get("/api/v1/models", response_model=ModelsResponse, tags=["Models"])
async def list_models():
    """获取支持的模型列表"""
    models = [
        ModelInfo(name="ollama/gemma3", type="local", description="Ollama - gemma3 模型（本地运行）"),
        ModelInfo(
            name="ollama/llama3.1:8b",
            type="local",
            description="Ollama - llama3.1 8B 模型（本地运行）",
        ),
        ModelInfo(
            name="ollama/deepseek-r1:7b",
            type="local",
            description="Ollama - deepseek-r1 7B 模型（本地运行）",
        ),
        ModelInfo(name="gpt-4o", type="cloud", description="OpenAI - GPT-4o 模型（需要 API Key）"),
        ModelInfo(
            name="gpt-3.5-turbo",
            type="cloud",
            description="OpenAI - GPT-3.5 Turbo 模型（需要 API Key）",
        ),
        ModelInfo(
            name="claude-3-opus",
            type="cloud",
            description="Anthropic - Claude 3 Opus 模型（需要 API Key）",
        ),
    ]

    return ModelsResponse(models=models)


# 获取 RAG 系统信息
@app.get("/api/v1/rag/info", tags=["RAG"])
async def rag_info():
    """获取 RAG 系统信息"""
    try:
        rag_system = get_rag_system()

        # 尝试获取集合信息
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


# 删除 RAG 向量存储
@app.delete("/api/v1/rag/clear", tags=["RAG"])
async def rag_clear():
    """清空 RAG 向量存储"""
    try:
        rag_system = get_rag_system()
        rag_system.delete_collection()

        global rag_system_instance
        rag_system_instance = None

        logger.info("RAG vector store cleared")

        return {"message": "Vector store cleared successfully"}

    except Exception as e:
        logger.error(f"Error clearing RAG: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    # nosec B104: 绑定到 0.0.0.0 用于开发环境，生产环境应使用具体 IP
    uvicorn.run(app, host="0.0.0.0", port=8000)
