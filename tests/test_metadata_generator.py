"""Tests for metadata_generator module."""

from unittest.mock import Mock, patch

import pytest
from langchain_core.documents import Document

from langchain_llm_toolkit.metadata_generator import DocumentMetadataGenerator


@pytest.fixture
def gen():
    """Create a generator with mocked LLM."""
    with patch("langchain_llm_toolkit.metadata_generator.LLMIntegration"):
        return DocumentMetadataGenerator(llm_model="test-model")


class TestExtractTitle:
    """Tests for _extract_title method."""

    def test_from_heading(self, gen):
        """Extract title from markdown heading."""
        title = gen._extract_title("# My Document Title\ncontent", "file.md")
        assert title == "My Document Title"

    def test_from_filename(self, gen):
        """Extract title from filename when no heading."""
        title = gen._extract_title("just content", "/path/to/my_document.txt")
        assert title == "my document"

    def test_from_filename_no_ext(self, gen):
        """Extract title from filename without extension."""
        title = gen._extract_title("content", "README")
        assert title == "README"

    def test_from_source_with_hyphens(self, gen):
        """Extract title from filename with hyphens."""
        title = gen._extract_title("content", "my-awesome-doc.md")
        assert title == "my awesome doc"

    def test_heading_takes_priority(self, gen):
        """Heading should take priority over filename."""
        title = gen._extract_title("# Real Title\ncontent", "filename.md")
        assert title == "Real Title"


class TestParseResponse:
    """Tests for _parse_response method."""

    def test_valid_json(self, gen):
        """Parse valid JSON response."""
        response = '{"name": "Test", "description": "Desc", "tags": ["a"], "category": "cat"}'
        result = gen._parse_response(response)
        assert result["name"] == "Test"
        assert result["description"] == "Desc"
        assert result["tags"] == ["a"]
        assert result["category"] == "cat"

    def test_json_with_extra_text(self, gen):
        """Parse JSON surrounded by extra text."""
        response = 'Here is the result: {"name": "X", "description": "Y", "tags": ["t"], "category": "c"} end'
        result = gen._parse_response(response)
        assert result["name"] == "X"

    def test_missing_fields(self, gen):
        """Test that missing fields get defaults."""
        response = '{"name": "Only"}'
        result = gen._parse_response(response)
        assert result["name"] == "Only"
        assert result["description"] == "暂无描述"
        assert result["tags"] == ["未分类"]
        assert result["category"] == "其他"

    def test_invalid_json(self, gen):
        """Test that invalid JSON raises ValueError."""
        with pytest.raises(ValueError):
            gen._parse_response("no json here at all")


class TestDefaultValue:
    """Tests for _get_default_value method."""

    def test_name_default(self, gen):
        assert gen._get_default_value("name") == "未命名文档"

    def test_description_default(self, gen):
        assert gen._get_default_value("description") == "暂无描述"

    def test_tags_default(self, gen):
        assert gen._get_default_value("tags") == ["未分类"]

    def test_category_default(self, gen):
        assert gen._get_default_value("category") == "其他"

    def test_unknown_field(self, gen):
        assert gen._get_default_value("unknown") == ""


class TestExtractTags:
    """Tests for _extract_tags_from_content method."""

    def test_find_tags(self, gen):
        """Find matching tags from content."""
        tags = gen._extract_tags_from_content("Python 是一种编程语言，用于 AI 开发")
        assert "Python" in tags
        assert "AI" in tags

    def test_max_five_tags(self, gen):
        """Should return at most 5 tags."""
        tags = gen._extract_tags_from_content(
            "Python TypeScript JavaScript React Vue AI LLM RAG ML 机器学习"
        )
        assert len(tags) <= 5

    def test_fallback_tag(self, gen):
        """Return fallback when no tags match."""
        tags = gen._extract_tags_from_content("nothing matches here")
        assert tags == ["未分类"]

    def test_case_insensitive(self, gen):
        """Tag matching should be case insensitive."""
        tags = gen._extract_tags_from_content("using python and react")
        assert "Python" in tags
        assert "React" in tags


class TestInferCategory:
    """Tests for _infer_category method."""

    def test_from_source_path(self, gen):
        """Infer category from source path."""
        cat = gen._infer_category("/docs/03-投资策略/report.md", "content")
        assert cat == "投资策略"

    def test_from_content_keywords(self, gen):
        """Infer category from content keywords."""
        cat = gen._infer_category("unknown.txt", "使用 Python 和 TypeScript 开发 API")
        assert cat == "技术实现"

    def test_financial_from_content(self, gen):
        """Infer financial from IRR keyword."""
        cat = gen._infer_category("data.csv", "投资产品 IRR 收益率分析")
        assert cat == "财务分析"

    def test_career_from_content(self, gen):
        """Infer career from resume keywords."""
        cat = gen._infer_category("file.txt", "面试经验和简历模板")
        assert cat == "职业发展"

    def test_default_category(self, gen):
        """Return default when nothing matches."""
        cat = gen._infer_category("misc.txt", "just some random text")
        assert cat == "其他"


class TestGenerateFallback:
    """Tests for _generate_fallback_metadata method."""

    def test_fallback_structure(self, gen):
        """Fallback metadata should have all required fields."""
        doc = Document(page_content="test content", metadata={"source": "test.md"})
        result = gen._generate_fallback_metadata(doc)
        assert "name" in result
        assert "description" in result
        assert "tags" in result
        assert "category" in result
        assert result["auto_generated"] is False
        assert result["source"] == "test.md"

    def test_fallback_truncates_title(self, gen):
        """Long titles should be truncated to 20 chars."""
        long_title = "a" * 50
        doc = Document(page_content=f"# {long_title}\ncontent", metadata={"source": "f.md"})
        result = gen._generate_fallback_metadata(doc)
        assert len(result["name"]) <= 20
