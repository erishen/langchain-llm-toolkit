#!/usr/bin/env python3
"""批量导入文档到 RAG 知识库"""

import argparse
import logging
from pathlib import Path

from langchain_llm_toolkit.metadata_generator import DocumentMetadataGenerator
from langchain_llm_toolkit.rag import RAGSystem

logger = logging.getLogger(__name__)


def _add_fallback_metadata(documents: list) -> list:
    """为文档添加备用元数据（不使用 LLM）"""
    generator = DocumentMetadataGenerator()
    for doc in documents:
        if "name" not in doc.metadata or not doc.metadata["name"]:
            metadata = generator._generate_fallback_metadata(doc)
            doc.metadata.update(metadata)
    return documents


def import_documents(
    docs_dir: str,
    patterns: list | None = None,
    embedding_model: str = "snowflake-arctic-embed2",
    llm_model: str = "ollama/gemma4",
    generate_metadata: bool = False,
):
    """批量导入文档

    Args:
        docs_dir: 文档目录
        patterns: 文件模式列表，默认为 ["*.md"]
        embedding_model: 嵌入模型名称
        llm_model: LLM 模型名称
        generate_metadata: 是否自动生成元数据
    """
    if patterns is None:
        patterns = ["*.md"]

    docs_path = Path(docs_dir)
    if not docs_path.exists():
        logger.error(f"目录不存在 {docs_dir}")
        return

    logger.info("正在初始化 RAG 系统...")
    logger.info(f"  嵌入模型: {embedding_model}")
    logger.info(f"  LLM 模型: {llm_model}")
    logger.info(f"  生成元数据: {'是' if generate_metadata else '否'}")

    rag = RAGSystem(
        vector_store_type="qdrant",
        embedding_type="ollama",
        embedding_model=embedding_model,
        llm_model=llm_model,
    )

    metadata_generator = None
    if generate_metadata:
        metadata_generator = DocumentMetadataGenerator(llm_model=llm_model)

    all_files = []
    for pattern in patterns:
        all_files.extend(docs_path.rglob(pattern))

    all_files = sorted(set(all_files))
    logger.info(f"找到 {len(all_files)} 个文件")

    if not all_files:
        logger.info("没有找到匹配的文件")
        return

    success_count = 0
    failed_count = 0

    for i, file_path in enumerate(all_files, 1):
        try:
            logger.info(f"[{i}/{len(all_files)}] 处理: {file_path.relative_to(docs_path)}")

            documents = rag.load_and_process_documents([str(file_path)])

            # 始终添加元数据（使用备用方法或 LLM）
            if generate_metadata and metadata_generator:
                logger.info("生成元数据 (LLM)...")
                documents = metadata_generator.generate_batch(documents, show_progress=False)
            else:
                documents = _add_fallback_metadata(documents)

            if rag.vector_store is None:
                rag.create_vector_store(documents)
            else:
                rag.add_documents(documents)

            success_count += 1

        except Exception as e:
            logger.error(f"处理文件失败: {e}")
            failed_count += 1

    rag.save_vector_store()

    logger.info("导入完成!")
    logger.info(f"  成功: {success_count}")
    logger.info(f"  失败: {failed_count}")

    try:
        info = rag.get_collection_info()
        logger.info(f"  向量数: {info.get('points_count', 'N/A')}")
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
  langchain-import ../.docs '*.md' --generate-metadata
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
        "--llm-model",
        "-l",
        default="ollama/gemma4",
        help="LLM 模型名称 (默认: ollama/gemma4)",
    )
    parser.add_argument(
        "--generate-metadata",
        "-g",
        action="store_true",
        help="自动生成文档元数据 (name, description, tags)",
    )

    args = parser.parse_args()

    import_documents(
        docs_dir=args.docs_dir,
        patterns=args.patterns,
        embedding_model=args.embedding_model,
        llm_model=args.llm_model,
        generate_metadata=args.generate_metadata,
    )


if __name__ == "__main__":
    main()
