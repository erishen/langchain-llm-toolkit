#!/usr/bin/env python
"""重建 profile-rag 双向量存储（FAISS + Qdrant），并按内容哈希去重。

背景：索引历史上从多个根目录多次导入，同一文件以不同相对路径重复入库
（investment/guide.md vs investment/raw/guide.md、投资备忘录.md 双路径等），
重复 chunk 会稀释 BM25/向量混合检索的排序。且源树（ts-demo/docs）已重组为
中文编号目录，旧相对路径不再指向磁盘上的真实文件——因此本脚本**不从源文件
重建**，而是从现有 FAISS docstore 取出全部 chunk，按内容去重后重建两套存储。

用法（必须先停掉主容器，Qdrant 本地模式有排他锁）：
    docker compose -f docker-compose.yml stop profile-rag
    docker run --rm -i \
        -v "$PWD/vector_store:/app/apps/langchain-llm-toolkit/vector_store" \
        -v "$PWD/qdrant_storage:/app/apps/langchain-llm-toolkit/qdrant_storage" \
        -e OLLAMA_BASE_URL="$OLLAMA_BASE_URL" \
        --entrypoint python profile-rag:latest - < scripts/rebuild_stores.py
    docker compose -f docker-compose.yml start profile-rag

可选参数（脚本顶部常量）：
    DEDUPE_KEEP_PREFER_NO_RAW  去重时优先保留路径不含 /raw/ 的代表 chunk
"""

import hashlib
import logging
import os
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("rebuild_stores")

FAISS_DIR = os.environ.get("RAG_FAISS_PATH", "/app/apps/langchain-llm-toolkit/vector_store")
QDRANT_DIR = os.environ.get("RAG_QDRANT_PATH", "/app/apps/langchain-llm-toolkit/qdrant_storage")
COLLECTION = os.environ.get("RAG_COLLECTION_NAME", "langchain_documents")
EMBED_MODEL = os.environ.get("EMBEDDING_MODEL", "snowflake-arctic-embed2")
PREFER_NO_RAW = True


def main() -> int:
    from langchain_community.vectorstores import FAISS, Qdrant
    from qdrant_client import QdrantClient

    from langchain_llm_toolkit.rag import OllamaEmbeddingsWrapper

    base_url = os.environ.get("OLLAMA_BASE_URL")
    if not base_url:
        logger.error("OLLAMA_BASE_URL 未设置，无法初始化 ollama embedding")
        return 1
    embeddings = OllamaEmbeddingsWrapper(model=EMBED_MODEL, base_url=base_url, num_ctx=8192)

    # 1) 从现有 FAISS docstore 取出全部 chunk
    logger.info(f"加载 FAISS: {FAISS_DIR}")
    store = FAISS.load_local(FAISS_DIR, embeddings, allow_dangerous_deserialization=True)
    all_docs = list(store.docstore._dict.values())
    logger.info(f"现有 chunk: {len(all_docs)}")

    # 2) 按 sha1(page_content) 分组去重；代表 chunk 优先选路径不含 /raw/ 且更短的
    groups: dict[str, list] = {}
    for doc in all_docs:
        key = hashlib.sha1(doc.page_content.encode("utf-8")).hexdigest()
        groups.setdefault(key, []).append(doc)

    def rank(doc) -> tuple:
        src = str((doc.metadata or {}).get("source", ""))
        return (1 if (PREFER_NO_RAW and "/raw/" in src) else 0, len(src), src)

    unique_docs, dup_groups = [], 0
    for docs in groups.values():
        if len(docs) > 1:
            dup_groups += 1
            srcs = sorted({str((d.metadata or {}).get("source", "?")) for d in docs})
            logger.info(f"重复组({len(docs)}): {srcs} → 保留 {min(docs, key=rank).metadata.get('source')}")
        unique_docs.append(min(docs, key=rank))

    logger.info(f"去重后 chunk: {len(unique_docs)} (删除 {len(all_docs) - len(unique_docs)}，重复组 {dup_groups})")
    if not unique_docs:
        logger.error("去重后为空，中止")
        return 1

    # 3) 重建 FAISS（原 chunk 不再切分，保持边界与 embedding 一致）
    faiss_new = FAISS.from_documents(unique_docs, embeddings)
    faiss_new.save_local(FAISS_DIR)
    logger.info(f"FAISS 已重建并保存: {FAISS_DIR} ({len(unique_docs)} chunks)")

    # 4) 重建 Qdrant 集合（delete + create + add，自动持久化）
    client = QdrantClient(path=QDRANT_DIR)
    from qdrant_client.http import models as rest

    sample = embeddings.embed_query("dim-check")
    client.delete_collection(collection_name=COLLECTION)
    client.create_collection(
        collection_name=COLLECTION,
        vectors_config=rest.VectorParams(size=len(sample), distance=rest.Distance.COSINE),
    )
    qdrant_new = Qdrant(client=client, collection_name=COLLECTION, embeddings=embeddings)
    qdrant_new.add_documents(unique_docs)
    count = client.count(COLLECTION, exact=True).count
    logger.info(f"Qdrant 集合 '{COLLECTION}' 已重建: {count} points ({QDRANT_DIR})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
