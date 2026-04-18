from typing import Dict, List, Any
from enum import Enum


class PromptTemplateType(Enum):
    """提示模板类型"""

    RAG_QA = "rag_qa"
    RAG_SUMMARY = "rag_summary"
    RAG_EXTRACT = "rag_extract"
    CHAT_SYSTEM = "chat_system"
    CHAT_USER = "chat_user"
    GENERATE_CODE = "generate_code"
    GENERATE_TEXT = "generate_text"
    TRANSLATE = "translate"
    SUMMARIZE = "summarize"


class PromptTemplate:
    """提示模板管理器"""

    def __init__(self):
        self.templates = self._load_default_templates()

    def _load_default_templates(self) -> Dict[str, str]:
        """加载默认提示模板"""
        return {
            # RAG 相关模板
            PromptTemplateType.RAG_QA.value: """你是一个专业的知识库问答助手。请基于以下上下文回答问题。

## 上下文文档
{context}

## 用户问题
{query}

## 回答要求
1. **准确性**: 只基于上下文回答，不要编造信息
2. **完整性**: 尽可能详细回答，涵盖上下文中的相关信息
3. **结构化**: 使用清晰的段落和要点组织回答
4. **引用**: 必要时标注信息来源（如"根据文档1..."）
5. **诚实性**: 如果上下文中没有相关信息，请明确说明"根据现有知识库，我无法回答这个问题"

## 回答格式
请按以下格式组织回答：

**直接回答**: [一句话概括答案]

**详细说明**:
[详细展开说明，可使用列表、段落等]

**相关要点**:
- 要点1
- 要点2
- ...

**信息来源**: [标注引用的文档编号]

---

请开始回答：""",
            PromptTemplateType.RAG_SUMMARY.value: """请总结以下文档的主要内容。

文档内容：
{context}

要求：
1. 提取关键信息和要点
2. 保持简洁明了
3. 突出重要细节
4. 使用清晰的结构

总结：""",
            PromptTemplateType.RAG_EXTRACT.value: """请从以下文档中提取{extract_type}。

文档内容：
{context}

要求：
1. 准确提取相关信息
2. 保持原始表述
3. 列出所有相关内容
4. 标注来源位置

提取结果：""",
            # 聊天相关模板
            PromptTemplateType.CHAT_SYSTEM.value: """你是一个{role}。

特点：
{characteristics}

能力：
{capabilities}

限制：
{limitations}

请根据这些设定与用户进行对话。""",
            PromptTemplateType.CHAT_USER.value: """{user_input}

背景信息：
{context}

请根据背景信息回答用户的问题。""",
            # 生成相关模板
            PromptTemplateType.GENERATE_CODE.value: """请根据以下要求生成代码。

需求：{requirement}

语言：{language}

要求：
1. 代码要清晰、规范
2. 添加必要的注释
3. 考虑边界情况
4. 提供使用示例

代码：""",
            PromptTemplateType.GENERATE_TEXT.value: """请根据以下要求生成文本。

主题：{topic}
类型：{text_type}
风格：{style}
长度：{length}

要求：
1. 内容要准确、有深度
2. 结构要清晰
3. 语言要流畅
4. 符合指定的风格和长度

文本：""",
            # 翻译模板
            PromptTemplateType.TRANSLATE.value: """请将以下文本从{source_lang}翻译成{target_lang}。

原文：
{text}

要求：
1. 保持原文的意思和语气
2. 使用地道的表达方式
3. 注意文化差异
4. 保持格式一致

翻译：""",
            # 总结模板
            PromptTemplateType.SUMMARIZE.value: """请总结以下内容。

内容：
{content}

总结要求：
1. 长度：{length}
2. 重点：{focus}
3. 风格：{style}

总结：""",
        }

    def get_template(self, template_type: PromptTemplateType) -> str:
        """获取模板"""
        template: str = self.templates.get(template_type.value, "")
        return template

    def render(self, template_type: PromptTemplateType, **kwargs) -> str:
        """
        渲染模板

        Args:
            template_type: 模板类型
            **kwargs: 模板参数

        Returns:
            渲染后的提示
        """
        template_str = self.get_template(template_type)
        if not template_str:
            raise ValueError(f"Template not found: {template_type}")

        try:
            return template_str.format(**kwargs)
        except Exception as e:
            raise ValueError(f"Failed to render template: {e}")

    def add_template(self, name: str, template: str):
        """添加自定义模板"""
        self.templates[name] = template

    def list_templates(self) -> List[str]:
        """列出所有模板"""
        return list(self.templates.keys())


class RAGPromptBuilder:
    """RAG 提示构建器"""

    def __init__(self):
        self.template_manager: PromptTemplate = PromptTemplate()

    def build_qa_prompt(
        self, query: str, documents: List[Any], max_context_length: int = 4000
    ) -> str:
        """
        构建问答提示

        Args:
            query: 用户问题
            documents: 相关文档列表
            max_context_length: 最大上下文长度

        Returns:
            构建好的提示
        """
        # 构建上下文
        context_parts = []
        current_length = 0

        for i, doc in enumerate(documents):
            content = doc.page_content if hasattr(doc, "page_content") else str(doc)

            # 检查长度限制
            if current_length + len(content) > max_context_length:
                break

            # 添加文档编号和内容
            context_parts.append(f"[文档 {i+1}]\n{content}\n")
            current_length += len(content)

        context = "\n".join(context_parts)

        # 渲染模板
        return self.template_manager.render(PromptTemplateType.RAG_QA, context=context, query=query)

    def build_summary_prompt(self, documents: List[Any], max_context_length: int = 6000) -> str:
        """构建总结提示"""
        context_parts = []
        current_length = 0

        for doc in documents:
            content = doc.page_content if hasattr(doc, "page_content") else str(doc)

            if current_length + len(content) > max_context_length:
                break

            context_parts.append(content)
            current_length += len(content)

        context = "\n\n".join(context_parts)

        return self.template_manager.render(PromptTemplateType.RAG_SUMMARY, context=context)

    def build_extraction_prompt(
        self, documents: List[Any], extract_type: str, max_context_length: int = 4000
    ) -> str:
        """构建提取提示"""
        context_parts = []
        current_length = 0

        for doc in documents:
            content = doc.page_content if hasattr(doc, "page_content") else str(doc)

            if current_length + len(content) > max_context_length:
                break

            context_parts.append(content)
            current_length += len(content)

        context = "\n\n".join(context_parts)

        return self.template_manager.render(
            PromptTemplateType.RAG_EXTRACT, context=context, extract_type=extract_type
        )


class ChatPromptBuilder:
    """聊天提示构建器"""

    def __init__(self):
        self.template_manager: PromptTemplate = PromptTemplate()

    def build_system_prompt(
        self,
        role: str = "智能助手",
        characteristics: str = "友好、专业、乐于助人",
        capabilities: str = "回答问题、提供建议、解决问题",
        limitations: str = "不能提供医疗、法律等专业建议",
    ) -> str:
        """构建系统提示"""
        return self.template_manager.render(
            PromptTemplateType.CHAT_SYSTEM,
            role=role,
            characteristics=characteristics,
            capabilities=capabilities,
            limitations=limitations,
        )

    def build_user_prompt(self, user_input: str, context: str = "") -> str:
        """构建用户提示"""
        return self.template_manager.render(
            PromptTemplateType.CHAT_USER,
            user_input=user_input,
            context=context if context else "无",
        )


# 预定义的角色模板
ROLE_TEMPLATES = {
    "assistant": {
        "role": "智能助手",
        "characteristics": "友好、专业、乐于助人、耐心",
        "capabilities": "回答问题、提供建议、解决问题、协助学习",
        "limitations": "不能提供医疗、法律等专业建议，不能访问实时数据",
    },
    "teacher": {
        "role": "专业教师",
        "characteristics": "耐心、循循善诱、善于举例、注重理解",
        "capabilities": "解答疑问、讲解概念、提供学习建议、设计练习",
        "limitations": "不能替学生完成作业，不能提供考试答案",
    },
    "developer": {
        "role": "资深开发者",
        "characteristics": "专业、严谨、注重最佳实践、善于解决问题",
        "capabilities": "代码审查、架构设计、问题排查、技术选型",
        "limitations": "不能直接访问生产环境，不能修改关键配置",
    },
    "writer": {
        "role": "专业写作顾问",
        "characteristics": "文笔优美、逻辑清晰、富有创意",
        "capabilities": "文案撰写、内容优化、创意构思、风格调整",
        "limitations": "不能抄袭他人作品，不能提供虚假信息",
    },
}


def get_prompt_template() -> PromptTemplate:
    """获取提示模板管理器"""
    return PromptTemplate()


def get_rag_prompt_builder() -> RAGPromptBuilder:
    """获取 RAG 提示构建器"""
    return RAGPromptBuilder()


def get_chat_prompt_builder() -> ChatPromptBuilder:
    """获取聊天提示构建器"""
    return ChatPromptBuilder()
