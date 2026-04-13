from typing import List, Union
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter, CharacterTextSplitter


class TextSplitter:
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
            method: 分割方法，支持 "recursive" 和 "character"

        Returns:
            分割后的文档片段列表
        """
        splitter: Union[RecursiveCharacterTextSplitter, CharacterTextSplitter]
        if method == "recursive":
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                separators=["\n\n", "\n", " ", ""],
            )
        elif method == "character":
            splitter = CharacterTextSplitter(
                chunk_size=chunk_size, chunk_overlap=chunk_overlap, separator=""
            )
        else:
            raise ValueError(f"不支持的分割方法: {method}")

        return splitter.split_documents(documents)

    def split_text(
        self, text: str, chunk_size: int = 1000, chunk_overlap: int = 200, method: str = "recursive"
    ) -> List[str]:
        """分割文本为更小的片段

        Args:
            text: 要分割的文本
            chunk_size: 每个片段的最大长度
            chunk_overlap: 片段之间的重叠长度
            method: 分割方法，支持 "recursive" 和 "character"

        Returns:
            分割后的文本片段列表
        """
        splitter: Union[RecursiveCharacterTextSplitter, CharacterTextSplitter]
        if method == "recursive":
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                separators=["\n\n", "\n", " ", ""],
            )
        elif method == "character":
            splitter = CharacterTextSplitter(
                chunk_size=chunk_size, chunk_overlap=chunk_overlap, separator=""
            )
        else:
            raise ValueError(f"不支持的分割方法: {method}")

        return splitter.split_text(text)
