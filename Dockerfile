# syntax=docker/dockerfile:1
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TZ=Asia/Shanghai \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends libmagic1 \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir uv

WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY libs/investkit_utils/ ./libs/investkit_utils/
COPY apps/langchain-llm-toolkit/pyproject.toml ./apps/langchain-llm-toolkit/
COPY apps/langchain-llm-toolkit/README.md ./apps/langchain-llm-toolkit/
COPY apps/langchain-llm-toolkit/src/ ./apps/langchain-llm-toolkit/src/

WORKDIR /app/apps/langchain-llm-toolkit
RUN uv sync --package langchain-llm-toolkit --no-dev --no-cache

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=5 \
    CMD python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8001/health',timeout=3)"

CMD ["uvicorn", "langchain_llm_toolkit.api:app", "--host", "0.0.0.0", "--port", "8001"]
