"""文档分块模块 - 支持多种分块策略"""

from typing import List, Union
from langchain_core.documents import Document
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    CharacterTextSplitter,
    MarkdownHeaderTextSplitter,
)


class TextSplitter:
    """文档分块器 - 支持多种分块策略"""

    def __init__(self):
        pass

    def split_documents(
        self,
        documents: List[Document],
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        method: str = "recursive",
    ) -> List[Document]:
        """分割文档为更小的片段

        Args:
            documents: 文档对象列表
            chunk_size: 每个片段的最大长度
            chunk_overlap: 片段之间的重叠长度
            method: 分割方法，支持 "recursive", "character", "markdown", "semantic"

        Returns:
            分割后的文档片段列表
        """
        if method == "markdown":
            return self._split_markdown(documents, chunk_size, chunk_overlap)
        elif method == "semantic":
            return self._split_semantic(documents, chunk_size, chunk_overlap)
        else:
            splitter: Union[RecursiveCharacterTextSplitter, CharacterTextSplitter]
            if method == "recursive":
                splitter = RecursiveCharacterTextSplitter(
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    separators=["\n\n", "\n", "。", "！", "？", "；", " ", ""],
                )
            elif method == "character":
                splitter = CharacterTextSplitter(
                    chunk_size=chunk_size, chunk_overlap=chunk_overlap, separator=""
                )
            else:
                raise ValueError(f"不支持的分割方法: {method}")

            return splitter.split_documents(documents)

    def _split_markdown(
        self, documents: List[Document], chunk_size: int, chunk_overlap: int
    ) -> List[Document]:
        """Markdown 分块 - 按标题层级分割

        优点：
        - 保持文档结构完整性
        - 每个块有明确的主题
        - 适合技术文档
        """
        headers_to_split_on = [
            ("#", "header1"),
            ("##", "header2"),
            ("###", "header3"),
            ("####", "header4"),
        ]

        markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=headers_to_split_on,
            strip_headers=False,
        )

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", "。", " ", ""],
        )

        all_chunks = []
        for doc in documents:
            try:
                md_chunks = markdown_splitter.split_text(doc.page_content)
                for chunk in md_chunks:
                    chunk.metadata.update(doc.metadata)
                all_chunks.extend(text_splitter.split_documents(md_chunks))
            except Exception:
                all_chunks.extend(text_splitter.split_documents([doc]))

        return all_chunks

    def _split_semantic(
        self, documents: List[Document], chunk_size: int, chunk_overlap: int
    ) -> List[Document]:
        """语义分块 - 按段落和句子边界分割

        优点：
        - 保持语义完整性
        - 避免切断句子
        - 更好的检索效果
        """
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=[
                "\n\n\n",
                "\n\n",
                "\n",
                "。",
                "！",
                "？",
                "；",
                "，",
                " ",
                "",
            ],
            is_separator_regex=False,
        )

        all_chunks = []
        for doc in documents:
            chunks = text_splitter.split_documents([doc])
            for chunk in chunks:
                chunk.metadata.update(doc.metadata)
            all_chunks.extend(chunks)

        return all_chunks

    def split_text(
        self, text: str, chunk_size: int = 1000, chunk_overlap: int = 200, method: str = "recursive"
    ) -> List[str]:
        """分割文本为更小的片段

        Args:
            text: 要分割的文本
            chunk_size: 每个片段的最大长度
            chunk_overlap: 片段之间的重叠长度
            method: 分割方法

        Returns:
            分割后的文本片段列表
        """
        doc = Document(page_content=text)
        chunks = self.split_documents([doc], chunk_size, chunk_overlap, method)
        return [chunk.page_content for chunk in chunks]

    def split_with_metadata(
        self,
        documents: List[Document],
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        method: str = "recursive",
        preserve_metadata: bool = True,
    ) -> List[Document]:
        """分割文档并保留元数据

        Args:
            documents: 文档对象列表
            chunk_size: 每个片段的最大长度
            chunk_overlap: 片段之间的重叠长度
            method: 分割方法
            preserve_metadata: 是否保留原始元数据

        Returns:
            分割后的文档片段列表
        """
        chunks = self.split_documents(documents, chunk_size, chunk_overlap, method)

        if preserve_metadata:
            for i, chunk in enumerate(chunks):
                chunk.metadata["chunk_index"] = i
                chunk.metadata["chunk_method"] = method

        return chunks


def get_optimal_chunk_params(content_type: str) -> dict:
    """根据内容类型获取最佳分块参数

    Args:
        content_type: 内容类型 (markdown, code, article, qa)

    Returns:
        最佳参数配置
    """
    params = {
        "markdown": {
            "chunk_size": 1500,
            "chunk_overlap": 200,
            "method": "markdown",
        },
        "code": {
            "chunk_size": 1000,
            "chunk_overlap": 100,
            "method": "recursive",
        },
        "article": {
            "chunk_size": 1200,
            "chunk_overlap": 200,
            "method": "semantic",
        },
        "qa": {
            "chunk_size": 800,
            "chunk_overlap": 100,
            "method": "semantic",
        },
    }

    return params.get(content_type, params["article"])
