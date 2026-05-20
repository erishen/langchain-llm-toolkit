import os
import tempfile

import pytest

from langchain_llm_toolkit.document_loader import DocumentLoader
from langchain_llm_toolkit.markdown_loader import MarkdownLoader


class TestMarkdownLoader:
    """测试 Markdown 加载器"""

    @pytest.fixture
    def loader(self):
        return MarkdownLoader()

    @pytest.fixture
    def sample_markdown(self):
        return """---
title: 测试文档
author: 测试作者
date: 2024-01-01
tags: [测试, markdown]
---

# 主标题

这是主标题下的内容。

## 二级标题 A

这是二级标题 A 的内容。

```python
def hello():
    print("Hello, World!")
```

### 三级标题

这是三级标题的内容。

## 二级标题 B

这是二级标题 B 的内容。

| 列1 | 列2 | 列3 |
|-----|-----|-----|
| A   | B   | C   |
| D   | E   | F   |

[链接文本](https://example.com)

![图片描述](https://example.com/image.png)
"""

    def test_load_with_front_matter(self, loader, sample_markdown):
        """测试加载带 front matter 的文档"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(sample_markdown)
            f.flush()

            try:
                documents = loader.load(f.name)

                assert len(documents) > 0
                assert documents[0].metadata.get("title") == "测试文档"
                assert documents[0].metadata.get("author") == "测试作者"
                assert documents[0].metadata.get("tags") == ["测试", "markdown"]
            finally:
                os.unlink(f.name)

    def test_split_by_heading(self, loader, sample_markdown):
        """测试按标题分割"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(sample_markdown)
            f.flush()

            try:
                documents = loader.load(f.name)

                heading_titles = [
                    doc.metadata.get("heading_title") for doc in documents
                ]
                assert "主标题" in heading_titles
                assert "二级标题 A" in heading_titles
                assert "二级标题 B" in heading_titles
            finally:
                os.unlink(f.name)

    def test_extract_code_blocks(self, loader, sample_markdown):
        """测试提取代码块"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(sample_markdown)
            f.flush()

            try:
                documents = loader.load(f.name)

                code_doc = None
                for doc in documents:
                    if doc.metadata.get("heading_title") == "二级标题 A":
                        code_doc = doc
                        break

                assert code_doc is not None
                assert "code_blocks" in code_doc.metadata
                assert len(code_doc.metadata["code_blocks"]) == 1
                assert code_doc.metadata["code_blocks"][0]["language"] == "python"
            finally:
                os.unlink(f.name)

    def test_extract_tables(self, loader, sample_markdown):
        """测试提取表格"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(sample_markdown)
            f.flush()

            try:
                documents = loader.load(f.name)

                table_doc = None
                for doc in documents:
                    if doc.metadata.get("heading_title") == "二级标题 B":
                        table_doc = doc
                        break

                assert table_doc is not None
                assert "tables" in table_doc.metadata
                assert len(table_doc.metadata["tables"]) == 1
                assert table_doc.metadata["tables"][0]["row_count"] == 2
            finally:
                os.unlink(f.name)

    def test_extract_links(self, loader, sample_markdown):
        """测试提取链接"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(sample_markdown)
            f.flush()

            try:
                documents = loader.load(f.name)

                link_doc = None
                for doc in documents:
                    if doc.metadata.get("heading_title") == "二级标题 B":
                        link_doc = doc
                        break

                assert link_doc is not None
                assert "links" in link_doc.metadata
                assert len(link_doc.metadata["links"]) >= 1
                assert any(
                    link["text"] == "链接文本" for link in link_doc.metadata["links"]
                )
            finally:
                os.unlink(f.name)

    def test_extract_images(self, loader, sample_markdown):
        """测试提取图片"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(sample_markdown)
            f.flush()

            try:
                documents = loader.load(f.name)

                image_doc = None
                for doc in documents:
                    if doc.metadata.get("heading_title") == "二级标题 B":
                        image_doc = doc
                        break

                assert image_doc is not None
                assert "images" in image_doc.metadata
                assert len(image_doc.metadata["images"]) == 1
                assert image_doc.metadata["images"][0]["alt"] == "图片描述"
            finally:
                os.unlink(f.name)

    def test_get_document_outline(self, loader, sample_markdown):
        """测试获取文档大纲"""
        outline = loader.get_document_outline(sample_markdown)

        assert len(outline) == 4
        assert outline[0]["level"] == 1
        assert outline[0]["title"] == "主标题"

    def test_get_statistics(self, loader, sample_markdown):
        """测试获取统计信息"""
        stats = loader.get_statistics(sample_markdown)

        assert stats["heading_count"] == 4
        assert stats["code_block_count"] == 1
        assert stats["table_count"] == 1
        assert stats["link_count"] >= 1
        assert "python" in stats["code_languages"]

    def test_heading_level_filter(self):
        """测试标题级别过滤"""
        loader = MarkdownLoader(min_heading_level=2, max_heading_level=2)

        markdown = """# 一级标题
一级内容
## 二级标题 A
二级内容 A
### 三级标题
三级内容
## 二级标题 B
二级内容 B
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(markdown)
            f.flush()

            try:
                documents = loader.load(f.name)

                heading_titles = [
                    doc.metadata.get("heading_title") for doc in documents
                ]
                assert "一级标题" not in heading_titles
                assert "二级标题 A" in heading_titles
                assert "三级标题" not in heading_titles
                assert "二级标题 B" in heading_titles
            finally:
                os.unlink(f.name)

    def test_no_split_by_heading(self):
        """测试不按标题分割"""
        loader = MarkdownLoader(split_by_heading=False)

        markdown = """# 标题
内容
## 二级标题
更多内容
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(markdown)
            f.flush()

            try:
                documents = loader.load(f.name)

                assert len(documents) == 1
                assert "# 标题" in documents[0].page_content
            finally:
                os.unlink(f.name)


class TestDocumentLoaderMarkdown:
    """测试 DocumentLoader 的 Markdown 功能"""

    @pytest.fixture
    def loader(self):
        return DocumentLoader()

    def test_load_markdown_file(self, loader):
        """测试加载 Markdown 文件"""
        markdown = """# 测试文档

这是测试内容。

## 功能介绍

这是功能介绍的内容。
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(markdown)
            f.flush()

            try:
                documents = loader.load_document(f.name)

                assert len(documents) > 0
                assert documents[0].metadata["type"] == "markdown"
            finally:
                os.unlink(f.name)

    def test_get_markdown_outline(self, loader):
        """测试获取 Markdown 大纲"""
        markdown = """# 主标题
## 二级标题 A
### 三级标题
## 二级标题 B
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(markdown)
            f.flush()

            try:
                outline = loader.get_markdown_outline(f.name)

                assert len(outline) == 4
                assert outline[0]["level"] == 1
                assert outline[1]["level"] == 2
            finally:
                os.unlink(f.name)

    def test_get_markdown_statistics(self, loader):
        """测试获取 Markdown 统计信息"""
        markdown = """# 测试文档

```python
print("hello")
```

| A | B |
|---|---|
| 1 | 2 |

[链接](https://example.com)
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(markdown)
            f.flush()

            try:
                stats = loader.get_markdown_statistics(f.name)

                assert stats["heading_count"] == 1
                assert stats["code_block_count"] == 1
                assert stats["table_count"] == 1
                assert stats["link_count"] == 1
            finally:
                os.unlink(f.name)

    def test_load_documents_batch(self, loader):
        """测试批量加载文档"""
        markdown1 = """# 文档1
内容1
"""
        markdown2 = """# 文档2
内容2
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f1, \
             tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f2:
            f1.write(markdown1)
            f2.write(markdown2)
            f1.flush()
            f2.flush()

            try:
                documents = loader.load_documents([f1.name, f2.name])

                assert len(documents) >= 2
            finally:
                os.unlink(f1.name)
                os.unlink(f2.name)
