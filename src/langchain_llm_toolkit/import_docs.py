#!/usr/bin/env python3
"""批量导入文档到 RAG 知识库"""

import argparse
from pathlib import Path

from langchain_llm_toolkit.rag import RAGSystem


def import_documents(
    docs_dir: str,
    patterns: list = None,
    embedding_model: str = "snowflake-arctic-embed2",
    llm_model: str = "ollama/gemma4",
):
    """批量导入文档

    Args:
        docs_dir: 文档目录
        patterns: 文件模式列表，默认为 ["*.md"]
        embedding_model: 嵌入模型名称
        llm_model: LLM 模型名称
    """
    if patterns is None:
        patterns = ["*.md"]

    docs_path = Path(docs_dir)
    if not docs_path.exists():
        print(f"Error: 目录不存在 {docs_dir}")
        return

    print("正在初始化 RAG 系统...")
    print(f"  嵌入模型: {embedding_model}")
    print(f"  LLM 模型: {llm_model}")

    rag = RAGSystem(
        vector_store_type="qdrant",
        embedding_type="ollama",
        embedding_model=embedding_model,
        llm_model=llm_model,
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

    print("\n导入完成!")
    print(f"  成功: {success_count}")
    print(f"  失败: {failed_count}")

    try:
        info = rag.get_collection_info()
        print(f"  向量数: {info.get('points_count', 'N/A')}")
    except Exception:
        pass


def main():
    """入口点函数"""
    parser = argparse.ArgumentParser(
        description="批量导入文档到 RAG 知识库",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  langchain-import ../.docs '*.md'
  langchain-import ../.docs '*.md' '*.txt'
  langchain-import ../.docs '*.md' --embedding-model snowflake-arctic-embed2
        """,
    )
    parser.add_argument("docs_dir", help="文档目录路径")
    parser.add_argument("patterns", nargs="*", default=["*.md"], help="文件模式 (默认: *.md)")
    parser.add_argument(
        "--embedding-model",
        "-e",
        default="snowflake-arctic-embed2",
        help="嵌入模型名称 (默认: snowflake-arctic-embed2)",
    )
    parser.add_argument(
        "--llm-model", "-l", default="ollama/gemma4", help="LLM 模型名称 (默认: ollama/gemma4)"
    )

    args = parser.parse_args()

    import_documents(
        docs_dir=args.docs_dir,
        patterns=args.patterns,
        embedding_model=args.embedding_model,
        llm_model=args.llm_model,
    )


if __name__ == "__main__":
    main()
