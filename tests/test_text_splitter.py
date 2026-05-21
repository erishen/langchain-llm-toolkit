"""
Tests for Text Splitter.
文档分块器测试
"""

import pytest
from langchain_core.documents import Document
from langchain_llm_toolkit.text_splitter import (
    TextSplitter,
    get_optimal_chunk_params,
)


class TestTextSplitter:
    """测试文档分块器"""

    def test_init(self):
        """测试初始化"""
        splitter = TextSplitter()
        assert splitter is not None

    def test_split_documents_recursive(self):
        """测试递归分割"""
        splitter = TextSplitter()
        documents = [
            Document(page_content="这是第一段内容。" * 50, metadata={"source": "test"}),
            Document(page_content="这是第二段内容。" * 50, metadata={"source": "test"}),
        ]

        chunks = splitter.split_documents(
            documents, chunk_size=100, chunk_overlap=20, method="recursive"
        )

        assert len(chunks) > 0
        for chunk in chunks:
            assert len(chunk.page_content) <= 150

    def test_split_documents_character(self):
        """测试字符分割"""
        splitter = TextSplitter()
        documents = [
            Document(page_content="Test content " * 20, metadata={"source": "test"}),
        ]

        chunks = splitter.split_documents(
            documents, chunk_size=100, chunk_overlap=10, method="character"
        )

        assert len(chunks) > 0

    def test_split_documents_markdown(self):
        """测试 Markdown 分割"""
        splitter = TextSplitter()
        markdown_content = """# 标题一

这是标题一的内容。

## 标题二

这是标题二的内容。

### 标题三

这是标题三的内容。
"""
        documents = [Document(page_content=markdown_content, metadata={"source": "test"})]

        chunks = splitter.split_documents(
            documents, chunk_size=500, chunk_overlap=50, method="markdown"
        )

        assert len(chunks) > 0

    def test_split_documents_semantic(self):
        """测试语义分割"""
        splitter = TextSplitter()
        documents = [
            Document(
                page_content="第一句话。第二句话。第三句话。第四句话。第五句话。",
                metadata={"source": "test"},
            ),
        ]

        chunks = splitter.split_documents(
            documents, chunk_size=20, chunk_overlap=5, method="semantic"
        )

        assert len(chunks) > 0

    def test_split_documents_invalid_method(self):
        """测试无效分割方法"""
        splitter = TextSplitter()
        documents = [Document(page_content="Test", metadata={})]

        with pytest.raises(ValueError):
            splitter.split_documents(documents, method="invalid")

    def test_split_text(self):
        """测试分割文本"""
        splitter = TextSplitter()
        text = "这是一段测试文本。" * 50

        chunks = splitter.split_text(text, chunk_size=100, chunk_overlap=20)

        assert len(chunks) > 0
        assert all(isinstance(chunk, str) for chunk in chunks)

    def test_split_text_empty(self):
        """测试分割空文本"""
        splitter = TextSplitter()
        chunks = splitter.split_text("")
        assert len(chunks) == 0

    def test_split_with_metadata(self):
        """测试带元数据分割"""
        splitter = TextSplitter()
        documents = [
            Document(
                page_content="测试内容。" * 30,
                metadata={"source": "test", "author": "tester"},
            ),
        ]

        chunks = splitter.split_with_metadata(
            documents,
            chunk_size=100,
            chunk_overlap=20,
            preserve_metadata=True,
        )

        assert len(chunks) > 0
        for chunk in chunks:
            assert "chunk_index" in chunk.metadata
            assert "chunk_method" in chunk.metadata
            assert chunk.metadata["source"] == "test"

    def test_split_with_metadata_no_preserve(self):
        """测试不保留元数据分割"""
        splitter = TextSplitter()
        documents = [
            Document(
                page_content="测试内容。" * 30,
                metadata={"source": "test"},
            ),
        ]

        chunks = splitter.split_with_metadata(
            documents,
            chunk_size=100,
            chunk_overlap=20,
            preserve_metadata=False,
        )

        for chunk in chunks:
            assert "chunk_index" not in chunk.metadata


class TestGetOptimalChunkParams:
    """测试获取最佳分块参数"""

    def test_markdown_params(self):
        """测试 Markdown 参数"""
        params = get_optimal_chunk_params("markdown")
        assert params["chunk_size"] == 1500
        assert params["method"] == "markdown"

    def test_code_params(self):
        """测试代码参数"""
        params = get_optimal_chunk_params("code")
        assert params["chunk_size"] == 1000
        assert params["method"] == "recursive"

    def test_article_params(self):
        """测试文章参数"""
        params = get_optimal_chunk_params("article")
        assert params["chunk_size"] == 1200
        assert params["method"] == "semantic"

    def test_qa_params(self):
        """测试 QA 参数"""
        params = get_optimal_chunk_params("qa")
        assert params["chunk_size"] == 800
        assert params["method"] == "semantic"

    def test_unknown_params(self):
        """测试未知类型参数"""
        params = get_optimal_chunk_params("unknown")
        assert params == get_optimal_chunk_params("article")


class TestTextSplitterEdgeCases:
    """测试边界情况"""

    def test_single_character(self):
        """测试单字符"""
        splitter = TextSplitter()
        documents = [Document(page_content="A", metadata={})]

        chunks = splitter.split_documents(documents)
        assert len(chunks) == 1
        assert chunks[0].page_content == "A"

    def test_exact_chunk_size(self):
        """测试精确块大小"""
        splitter = TextSplitter()
        text = "A" * 100
        documents = [Document(page_content=text, metadata={})]

        chunks = splitter.split_documents(documents, chunk_size=100, chunk_overlap=0)
        assert len(chunks) >= 1

    def test_large_overlap(self):
        """测试大重叠"""
        splitter = TextSplitter()
        text = "A" * 100
        documents = [Document(page_content=text, metadata={})]

        chunks = splitter.split_documents(documents, chunk_size=50, chunk_overlap=40)
        assert len(chunks) > 1

    def test_empty_documents(self):
        """测试空文档列表"""
        splitter = TextSplitter()
        chunks = splitter.split_documents([])
        assert chunks == []

    def test_chinese_text(self):
        """测试中文文本"""
        splitter = TextSplitter()
        text = "这是中文测试文本。" * 20
        documents = [Document(page_content=text, metadata={})]

        chunks = splitter.split_documents(documents, chunk_size=50, chunk_overlap=10)
        assert len(chunks) > 0

    def test_mixed_language(self):
        """测试混合语言"""
        splitter = TextSplitter()
        text = "This is English. 这是中文。Mixed content 混合内容。"
        documents = [Document(page_content=text, metadata={})]

        chunks = splitter.split_documents(documents, chunk_size=30, chunk_overlap=5)
        assert len(chunks) > 0
