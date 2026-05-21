"""
Document Metadata Generator.
文档元数据生成器 - 使用 LLM 自动生成文档的 name、description、tags
"""

import json
import logging
import re

from langchain_core.documents import Document

from langchain_llm_toolkit.llm_integration import LLMIntegration

logger = logging.getLogger(__name__)


class DocumentMetadataGenerator:
    """文档元数据生成器

    使用 LLM 为文档自动生成：
    - name: 简短名称
    - description: 描述摘要
    - tags: 标签列表
    - category: 分类
    """

    SYSTEM_PROMPT = """你是一个文档分析专家。请分析给定的文档内容，生成以下元数据：

1. name: 简短的文档名称（5-15个字）
2. description: 文档描述摘要（30-50个字）
3. tags: 相关标签列表（3-5个标签）
4. category: 文档分类（如：技术实现、投资策略、财务分析、职业发展等）

请以 JSON 格式返回，格式如下：
{
    "name": "文档名称",
    "description": "文档描述",
    "tags": ["标签1", "标签2", "标签3"],
    "category": "分类"
}

只返回 JSON，不要其他内容。"""

    USER_PROMPT_TEMPLATE = """请分析以下文档内容：

---
标题: {title}
来源: {source}
内容摘要:
{content_summary}
---

请生成文档元数据。"""

    def __init__(self, llm_model: str = "ollama/gemma4", timeout: int = 60):
        """初始化元数据生成器

        Args:
            llm_model: LLM 模型名称
            timeout: 请求超时时间（秒）
        """
        self.llm = LLMIntegration(timeout=timeout)
        self.llm.set_model(llm_model)
        logger.info(f"Initialized DocumentMetadataGenerator with model: {llm_model}")

    def generate_metadata(
        self,
        document: Document,
        max_content_length: int = 2000,
    ) -> dict:
        """为文档生成元数据

        Args:
            document: 文档对象
            max_content_length: 最大内容长度

        Returns:
            元数据字典
        """
        content = document.page_content
        source = document.metadata.get("source", "unknown")
        title = self._extract_title(content, source)

        content_summary = content[:max_content_length]
        if len(content) > max_content_length:
            content_summary += "..."

        prompt = self.USER_PROMPT_TEMPLATE.format(
            title=title,
            source=source,
            content_summary=content_summary,
        )

        try:
            combined_prompt = f"{self.SYSTEM_PROMPT}\n\n{prompt}"
            response = self.llm.generate(combined_prompt)

            metadata = self._parse_response(response)

            metadata["auto_generated"] = True
            metadata["source"] = source

            logger.debug(f"Generated metadata for {source}: {metadata}")
            return metadata

        except Exception as e:
            logger.warning(f"Failed to generate metadata for {source}: {e}")
            return self._generate_fallback_metadata(document)

    def _extract_title(self, content: str, source: str) -> str:
        """从内容或来源提取标题"""
        heading_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if heading_match:
            return heading_match.group(1).strip()

        filename = source.rsplit("/", 1)[-1] if "/" in source else source

        title = re.sub(r"\.[^.]+$", "", filename)
        return title.replace("_", " ").replace("-", " ")

    def _parse_response(self, response: str) -> dict:
        """解析 LLM 响应"""
        json_match = re.search(r"\{[\s\S]*\}", response)
        if json_match:
            json_str = json_match.group(0)
            metadata = json.loads(json_str)

            required_fields = ["name", "description", "tags", "category"]
            for field in required_fields:
                if field not in metadata:
                    metadata[field] = self._get_default_value(field)

            return metadata

        raise ValueError("No valid JSON found in response")

    def _get_default_value(self, field: str):
        """获取字段默认值"""
        defaults = {
            "name": "未命名文档",
            "description": "暂无描述",
            "tags": ["未分类"],
            "category": "其他",
        }
        return defaults.get(field, "")

    def _generate_fallback_metadata(self, document: Document) -> dict:
        """生成备用元数据（当 LLM 生成失败时）"""
        content = document.page_content
        source = document.metadata.get("source", "unknown")
        title = self._extract_title(content, source)

        tags = self._extract_tags_from_content(content)

        category = self._infer_category(source, content)

        return {
            "name": title[:20] if len(title) > 20 else title,
            "description": content[:50].replace("\n", " ") + "...",
            "tags": tags,
            "category": category,
            "auto_generated": False,
            "source": source,
        }

    def _extract_tags_from_content(self, content: str) -> list:
        """从内容中提取标签"""
        keywords = [
            "IRR",
            "收益率",
            "投资",
            "股票",
            "基金",
            "REITs",
            "Python",
            "TypeScript",
            "JavaScript",
            "React",
            "Vue",
            "机器学习",
            "ML",
            "AI",
            "LLM",
            "RAG",
            "职业",
            "面试",
            "简历",
            "LinkedIn",
            "财务",
            "资产",
            "收益",
            "风险",
        ]

        found_tags = []
        content_lower = content.lower()
        for keyword in keywords:
            if keyword.lower() in content_lower:
                found_tags.append(keyword)
            if len(found_tags) >= 5:
                break

        return found_tags if found_tags else ["未分类"]

    def _infer_category(self, source: str, content: str) -> str:
        """推断文档分类"""
        source_lower = source.lower()
        content_lower = content.lower()

        # 先按路径分类
        path_categories = {
            "职业发展": ["digital-persona", "linkedin", "career", "04-职业发展"],
            "投资策略": ["投资策略", "03-投资策略"],
            "财务分析": ["财务分析", "01-财务分析"],
            "技术实现": ["技术实现", "02-技术实现", "analysis"],
            "AI与数字化": ["ai与数字化", "04-ai与数字化"],
        }

        for category, path_keywords in path_categories.items():
            for keyword in path_keywords:
                if keyword in source_lower:
                    return category

        # 再按内容分类
        content_categories = {
            "职业发展": ["职业", "面试", "简历", "linkedin", "求职", "tech-stack"],
            "投资策略": ["投资策略", "定投", "reits"],
            "财务分析": ["财务", "资产详情", "年化", "盈亏", "财富积累"],
            "技术实现": ["技术实现", "python", "typescript", "api", "修复", "优化"],
            "AI与数字化": ["ai", "llm", "rag", "机器学习"],
        }

        for category, keywords in content_categories.items():
            for keyword in keywords:
                if keyword in content_lower:
                    return category

        # 默认分类
        if "irr" in content_lower or "收益" in content_lower:
            return "财务分析"
        if "投资" in content_lower or "备忘" in content_lower:
            return "投资策略"

        return "其他"

    def generate_batch(
        self,
        documents: list,
        max_content_length: int = 2000,
        show_progress: bool = True,
    ) -> list:
        """批量为文档生成元数据

        Args:
            documents: 文档列表
            max_content_length: 最大内容长度
            show_progress: 是否显示进度

        Returns:
            带元数据的文档列表
        """
        enriched_documents = []

        for i, doc in enumerate(documents):
            if show_progress:
                source = doc.metadata.get("source", "unknown")
                logger.info(f"[{i + 1}/{len(documents)}] 生成元数据: {source}")

            metadata = self.generate_metadata(doc, max_content_length)

            enriched_doc = Document(
                page_content=doc.page_content,
                metadata={**doc.metadata, **metadata},
            )
            enriched_documents.append(enriched_doc)

        return enriched_documents
