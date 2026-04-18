#!/usr/bin/env python3
"""批量导入文档到 RAG 知识库"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from langchain_llm_toolkit.rag import RAGSystem


def import_documents(docs_dir: str, patterns: list = None):
    """批量导入文档

    Args:
        docs_dir: 文档目录
        patterns: 文件模式列表，默认为 ["*.md", "*.pdf", "*.txt"]
    """
    if patterns is None:
        patterns = ["*.md"]

    docs_path = Path(docs_dir)
    if not docs_path.exists():
        print(f"Error: 目录不存在 {docs_dir}")
        return

    print(f"正在初始化 RAG 系统...")
    rag = RAGSystem(
        vector_store_type="qdrant",
        embedding_type="ollama",
        embedding_model="nomic-embed-text",
        llm_model="ollama/gemma3",
    )

    all_files = []
    for pattern in patterns:
        all_files.extend(docs_path.rglob(pattern))

    all_files = sorted(set(all_files))
    print(f"找到 {len(all_files)} 个文件")

    if not all_files:
        print("没有找到匹配的文件")
        return

    success_count = 0
    failed_count = 0

    for i, file_path in enumerate(all_files, 1):
        try:
            print(f"[{i}/{len(all_files)}] 处理: {file_path.relative_to(docs_path)}")

            documents = rag.load_and_process_documents([str(file_path)])

            if rag.vector_store is None:
                rag.create_vector_store(documents)
            else:
                rag.add_documents(documents)

            success_count += 1

        except Exception as e:
            print(f"  Error: {e}")
            failed_count += 1

    rag.save_vector_store()

    print(f"\n导入完成!")
    print(f"  成功: {success_count}")
    print(f"  失败: {failed_count}")

    try:
        info = rag.get_collection_info()
        print(f"  向量数: {info.get('points_count', 'N/A')}")
    except Exception:
        pass


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python import_docs.py <docs_dir> [patterns...]")
        print("Example: python import_docs.py ../.docs '*.md' '*.txt'")
        sys.exit(1)

    docs_dir = sys.argv[1]
    patterns = sys.argv[2:] if len(sys.argv) > 2 else None

    import_documents(docs_dir, patterns)
