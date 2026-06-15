import os
import re
from typing import Any

from langchain_core.documents import Document


class MarkdownLoader:
    """Markdown 文档加载器

    功能：
    - 按标题分割文档
    - 提取 YAML front matter 元数据
    - 处理代码块（识别语言）
    - 处理表格
    - 提取链接和图片信息
    """

    HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
    CODE_BLOCK_PATTERN = re.compile(r"```(\w*)\n(.*?)```", re.DOTALL)
    TABLE_PATTERN = re.compile(r"^\|.+\|$\n^\|[-:| ]+\|$\n(?:^\|.+\|$\n?)+", re.MULTILINE)
    LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
    IMAGE_PATTERN = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
    FRONT_MATTER_PATTERN = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)

    def __init__(
        self,
        split_by_heading: bool = True,
        extract_metadata: bool = True,
        extract_code_blocks: bool = True,
        extract_tables: bool = True,
        min_heading_level: int = 1,
        max_heading_level: int = 6,
    ):
        """
        初始化 Markdown 加载器

        Args:
            split_by_heading: 是否按标题分割文档
            extract_metadata: 是否提取元数据
            extract_code_blocks: 是否提取代码块
            extract_tables: 是否提取表格
            min_heading_level: 最小标题级别（1-6）
            max_heading_level: 最大标题级别（1-6）
        """
        self.split_by_heading = split_by_heading
        self.extract_metadata = extract_metadata
        self.extract_code_blocks = extract_code_blocks
        self.extract_tables = extract_tables
        self.min_heading_level = max(1, min(6, min_heading_level))
        self.max_heading_level = max(1, min(6, max_heading_level))

    def load(self, file_path: str) -> list[Document]:
        """加载 Markdown 文档"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        with open(file_path, encoding="utf-8", errors="ignore") as f:
            content = f.read()

        return self._parse_markdown(content, file_path)

    def _parse_markdown(self, content: str, file_path: str) -> list[Document]:
        """解析 Markdown 内容"""
        front_matter = {}
        if self.extract_metadata:
            content, front_matter = self._extract_front_matter(content)

        if self.split_by_heading:
            return self._split_by_headings(content, file_path, front_matter)
        else:
            return [self._create_document(content, file_path, front_matter)]

    def _extract_front_matter(self, content: str) -> tuple:
        """提取 YAML front matter"""
        match = self.FRONT_MATTER_PATTERN.match(content)
        if match:
            front_matter_text = match.group(1)
            front_matter = self._parse_yaml_front_matter(front_matter_text)
            content = content[match.end() :]
            return content, front_matter
        return content, {}

    def _parse_yaml_front_matter(self, text: str) -> dict[str, Any]:
        """解析 YAML front matter"""
        metadata = {}
        for line in text.split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()
                if value.startswith("[") and value.endswith("]"):
                    value = [v.strip() for v in value[1:-1].split(",")]
                elif value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.lower() == "true":
                    value = True
                elif value.lower() == "false":
                    value = False
                elif value.isdigit():
                    value = int(value)
                metadata[key] = value
        return metadata

    def _split_by_headings(self, content: str, file_path: str, front_matter: dict[str, Any]) -> list[Document]:
        """按标题分割文档"""
        headings = list(self.HEADING_PATTERN.finditer(content))

        if not headings:
            return [self._create_document(content, file_path, front_matter)]

        documents = []

        for i, match in enumerate(headings):
            level = len(match.group(1))
            title = match.group(2).strip()

            if level < self.min_heading_level or level > self.max_heading_level:
                continue

            start = match.end()
            end = headings[i + 1].start() if i + 1 < len(headings) else len(content)

            section_content = content[start:end].strip()

            if not section_content:
                continue

            metadata = {
                **front_matter,
                "source": file_path,
                "type": "markdown",
                "heading_level": level,
                "heading_title": title,
                "section_index": i,
            }

            if self.extract_code_blocks:
                code_blocks = self._extract_code_blocks(section_content)
                if code_blocks:
                    metadata["code_blocks"] = code_blocks
                    metadata["code_languages"] = list(set(cb["language"] for cb in code_blocks if cb["language"]))

            if self.extract_tables:
                tables = self._extract_tables(section_content)
                if tables:
                    metadata["tables"] = tables

            links = self._extract_links(section_content)
            if links:
                metadata["links"] = links

            images = self._extract_images(section_content)
            if images:
                metadata["images"] = images

            doc = Document(page_content=section_content, metadata=metadata)
            documents.append(doc)

        return documents

    def _create_document(self, content: str, file_path: str, front_matter: dict[str, Any]) -> Document:
        """创建单个文档"""
        metadata = {
            **front_matter,
            "source": file_path,
            "type": "markdown",
        }

        if self.extract_code_blocks:
            code_blocks = self._extract_code_blocks(content)
            if code_blocks:
                metadata["code_blocks"] = code_blocks

        if self.extract_tables:
            tables = self._extract_tables(content)
            if tables:
                metadata["tables"] = tables

        links = self._extract_links(content)
        if links:
            metadata["links"] = links

        images = self._extract_images(content)
        if images:
            metadata["images"] = images

        return Document(page_content=content, metadata=metadata)

    def _extract_code_blocks(self, content: str) -> list[dict[str, str]]:
        """提取代码块"""
        code_blocks = []
        for match in self.CODE_BLOCK_PATTERN.finditer(content):
            language = match.group(1) or "unknown"
            code = match.group(2).strip()
            code_blocks.append(
                {
                    "language": language,
                    "code": code[:200] + "..." if len(code) > 200 else code,
                    "length": len(code),
                }
            )
        return code_blocks

    def _extract_tables(self, content: str) -> list[dict[str, Any]]:
        """提取表格"""
        tables = []
        for match in self.TABLE_PATTERN.finditer(content):
            table_text = match.group(0)
            lines = [line for line in table_text.strip().split("\n") if line.strip()]
            if len(lines) >= 2:
                headers = [cell.strip() for cell in lines[0].split("|") if cell.strip()]
                rows = []
                for line in lines[2:]:
                    row = [cell.strip() for cell in line.split("|") if cell.strip()]
                    if row:
                        rows.append(row)
                tables.append(
                    {
                        "headers": headers,
                        "row_count": len(rows),
                        "column_count": len(headers),
                    }
                )
        return tables

    def _extract_links(self, content: str) -> list[dict[str, str]]:
        """提取链接"""
        links = [{"text": match.group(1), "url": match.group(2)} for match in self.LINK_PATTERN.finditer(content)]
        return links[:20]

    def _extract_images(self, content: str) -> list[dict[str, str]]:
        """提取图片"""
        images = [{"alt": match.group(1), "url": match.group(2)} for match in self.IMAGE_PATTERN.finditer(content)]
        return images[:10]

    def get_document_outline(self, content: str) -> list[dict[str, Any]]:
        """获取文档大纲"""
        outline = []
        for match in self.HEADING_PATTERN.finditer(content):
            level = len(match.group(1))
            title = match.group(2).strip()
            outline.append(
                {
                    "level": level,
                    "title": title,
                }
            )
        return outline

    def get_statistics(self, content: str) -> dict[str, Any]:
        """获取文档统计信息"""
        code_blocks = self._extract_code_blocks(content)
        tables = self._extract_tables(content)
        links = self._extract_links(content)
        images = self._extract_images(content)
        headings = list(self.HEADING_PATTERN.finditer(content))

        return {
            "total_characters": len(content),
            "total_words": len(content.split()),
            "total_lines": len(content.split("\n")),
            "heading_count": len(headings),
            "code_block_count": len(code_blocks),
            "table_count": len(tables),
            "link_count": len(links),
            "image_count": len(images),
            "code_languages": list(set(cb["language"] for cb in code_blocks if cb["language"])),
        }
