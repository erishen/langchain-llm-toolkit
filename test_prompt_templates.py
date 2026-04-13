import pytest
from unittest.mock import Mock

from prompt_templates import (
    PromptTemplateType,
    PromptTemplate,
    RAGPromptBuilder,
    ChatPromptBuilder,
    ROLE_TEMPLATES,
    get_prompt_template,
    get_rag_prompt_builder,
    get_chat_prompt_builder,
)


class TestPromptTemplateType:
    """测试提示模板类型枚举"""

    def test_enum_values(self):
        """测试枚举值"""
        assert PromptTemplateType.RAG_QA.value == "rag_qa"
        assert PromptTemplateType.RAG_SUMMARY.value == "rag_summary"
        assert PromptTemplateType.RAG_EXTRACT.value == "rag_extract"
        assert PromptTemplateType.CHAT_SYSTEM.value == "chat_system"
        assert PromptTemplateType.CHAT_USER.value == "chat_user"
        assert PromptTemplateType.GENERATE_CODE.value == "generate_code"
        assert PromptTemplateType.GENERATE_TEXT.value == "generate_text"
        assert PromptTemplateType.TRANSLATE.value == "translate"
        assert PromptTemplateType.SUMMARIZE.value == "summarize"


class TestPromptTemplate:
    """测试提示模板管理器"""

    def test_init(self):
        """测试初始化"""
        template = PromptTemplate()
        assert template.templates is not None
        assert len(template.templates) > 0

    def test_get_template_rag_qa(self):
        """测试获取 RAG QA 模板"""
        template = PromptTemplate()
        rag_template = template.get_template(PromptTemplateType.RAG_QA)
        assert "上下文" in rag_template
        assert "问题" in rag_template
        assert "{context}" in rag_template
        assert "{query}" in rag_template

    def test_get_template_chat_system(self):
        """测试获取聊天系统模板"""
        template = PromptTemplate()
        chat_template = template.get_template(PromptTemplateType.CHAT_SYSTEM)
        assert "{role}" in chat_template
        assert "{characteristics}" in chat_template
        assert "{capabilities}" in chat_template

    def test_render_rag_qa(self):
        """测试渲染 RAG QA 模板"""
        template = PromptTemplate()
        result = template.render(
            PromptTemplateType.RAG_QA, context="这是测试上下文", query="这是测试问题"
        )
        assert "这是测试上下文" in result
        assert "这是测试问题" in result
        assert "{context}" not in result
        assert "{query}" not in result

    def test_render_chat_system(self):
        """测试渲染聊天系统模板"""
        template = PromptTemplate()
        result = template.render(
            PromptTemplateType.CHAT_SYSTEM,
            role="AI助手",
            characteristics="友好、专业",
            capabilities="回答问题",
            limitations="不能提供专业建议",
        )
        assert "AI助手" in result
        assert "友好、专业" in result
        assert "回答问题" in result
        assert "不能提供专业建议" in result

    def test_render_translate(self):
        """测试渲染翻译模板"""
        template = PromptTemplate()
        result = template.render(
            PromptTemplateType.TRANSLATE, source_lang="中文", target_lang="英文", text="你好世界"
        )
        assert "中文" in result
        assert "英文" in result
        assert "你好世界" in result

    def test_render_summarize(self):
        """测试渲染总结模板"""
        template = PromptTemplate()
        result = template.render(
            PromptTemplateType.SUMMARIZE,
            content="测试内容",
            length="简短",
            focus="关键点",
            style="正式",
        )
        assert "测试内容" in result
        assert "简短" in result
        assert "关键点" in result
        assert "正式" in result

    def test_render_invalid_template(self):
        """测试渲染不存在的模板"""
        template = PromptTemplate()
        with pytest.raises(ValueError) as exc_info:
            template.render(PromptTemplateType.RAG_QA, wrong_param="test")
        assert "Failed to render template" in str(exc_info.value)

    def test_add_template(self):
        """测试添加自定义模板"""
        template = PromptTemplate()
        custom_template = "这是一个自定义模板：{param}"
        template.add_template("custom", custom_template)

        assert "custom" in template.templates
        assert template.templates["custom"] == custom_template

    def test_list_templates(self):
        """测试列出所有模板"""
        template = PromptTemplate()
        templates = template.list_templates()

        assert isinstance(templates, list)
        assert len(templates) > 0
        assert "rag_qa" in templates
        assert "chat_system" in templates


class TestRAGPromptBuilder:
    """测试 RAG 提示构建器"""

    def test_init(self):
        """测试初始化"""
        builder = RAGPromptBuilder()
        assert builder.template_manager is not None

    def test_build_qa_prompt(self):
        """测试构建问答提示"""
        builder = RAGPromptBuilder()

        doc1 = Mock()
        doc1.page_content = "文档1内容"

        doc2 = Mock()
        doc2.page_content = "文档2内容"

        result = builder.build_qa_prompt(query="测试问题", documents=[doc1, doc2])

        assert "测试问题" in result
        assert "文档1内容" in result
        assert "文档2内容" in result
        assert "[文档 1]" in result
        assert "[文档 2]" in result

    def test_build_qa_prompt_with_string_documents(self):
        """测试使用字符串文档构建问答提示"""
        builder = RAGPromptBuilder()

        result = builder.build_qa_prompt(query="测试问题", documents=["字符串文档1", "字符串文档2"])

        assert "测试问题" in result
        assert "字符串文档1" in result
        assert "字符串文档2" in result

    def test_build_qa_prompt_max_context_length(self):
        """测试最大上下文长度限制"""
        builder = RAGPromptBuilder()

        doc1 = Mock()
        doc1.page_content = "a" * 2000

        doc2 = Mock()
        doc2.page_content = "b" * 3000

        result = builder.build_qa_prompt(
            query="测试", documents=[doc1, doc2], max_context_length=2500
        )

        assert "a" * 2000 in result
        assert "b" * 3000 not in result

    def test_build_summary_prompt(self):
        """测试构建总结提示"""
        builder = RAGPromptBuilder()

        doc1 = Mock()
        doc1.page_content = "文档1"

        doc2 = Mock()
        doc2.page_content = "文档2"

        result = builder.build_summary_prompt([doc1, doc2])

        assert "文档1" in result
        assert "文档2" in result
        assert "总结" in result

    def test_build_extraction_prompt(self):
        """测试构建提取提示"""
        builder = RAGPromptBuilder()

        doc = Mock()
        doc.page_content = "测试文档内容"

        result = builder.build_extraction_prompt(documents=[doc], extract_type="关键信息")

        assert "测试文档内容" in result
        assert "关键信息" in result
        assert "提取" in result


class TestChatPromptBuilder:
    """测试聊天提示构建器"""

    def test_init(self):
        """测试初始化"""
        builder = ChatPromptBuilder()
        assert builder.template_manager is not None

    def test_build_system_prompt_default(self):
        """测试构建默认系统提示"""
        builder = ChatPromptBuilder()
        result = builder.build_system_prompt()

        assert "智能助手" in result
        assert "友好、专业、乐于助人" in result
        assert "回答问题、提供建议、解决问题" in result

    def test_build_system_prompt_custom(self):
        """测试构建自定义系统提示"""
        builder = ChatPromptBuilder()
        result = builder.build_system_prompt(
            role="专业教师",
            characteristics="耐心、专业",
            capabilities="教学、答疑",
            limitations="不能替学生完成作业",
        )

        assert "专业教师" in result
        assert "耐心、专业" in result
        assert "教学、答疑" in result
        assert "不能替学生完成作业" in result

    def test_build_user_prompt(self):
        """测试构建用户提示"""
        builder = ChatPromptBuilder()
        result = builder.build_user_prompt(user_input="你好", context="这是背景信息")

        assert "你好" in result
        assert "这是背景信息" in result

    def test_build_user_prompt_without_context(self):
        """测试构建无背景的用户提示"""
        builder = ChatPromptBuilder()
        result = builder.build_user_prompt(user_input="测试问题")

        assert "测试问题" in result
        assert "无" in result


class TestRoleTemplates:
    """测试预定义角色模板"""

    def test_role_templates_exist(self):
        """测试角色模板存在"""
        assert "assistant" in ROLE_TEMPLATES
        assert "teacher" in ROLE_TEMPLATES
        assert "developer" in ROLE_TEMPLATES
        assert "writer" in ROLE_TEMPLATES

    def test_assistant_template(self):
        """测试助手模板"""
        template = ROLE_TEMPLATES["assistant"]
        assert template["role"] == "智能助手"
        assert "characteristics" in template
        assert "capabilities" in template
        assert "limitations" in template

    def test_teacher_template(self):
        """测试教师模板"""
        template = ROLE_TEMPLATES["teacher"]
        assert template["role"] == "专业教师"
        assert "耐心" in template["characteristics"]

    def test_developer_template(self):
        """测试开发者模板"""
        template = ROLE_TEMPLATES["developer"]
        assert template["role"] == "资深开发者"
        assert "代码审查" in template["capabilities"]

    def test_writer_template(self):
        """测试写作顾问模板"""
        template = ROLE_TEMPLATES["writer"]
        assert template["role"] == "专业写作顾问"
        assert "文案撰写" in template["capabilities"]


class TestFactoryFunctions:
    """测试工厂函数"""

    def test_get_prompt_template(self):
        """测试获取提示模板管理器"""
        template = get_prompt_template()
        assert isinstance(template, PromptTemplate)

    def test_get_rag_prompt_builder(self):
        """测试获取 RAG 提示构建器"""
        builder = get_rag_prompt_builder()
        assert isinstance(builder, RAGPromptBuilder)

    def test_get_chat_prompt_builder(self):
        """测试获取聊天提示构建器"""
        builder = get_chat_prompt_builder()
        assert isinstance(builder, ChatPromptBuilder)

    def test_factory_returns_new_instances(self):
        """测试工厂函数返回新实例"""
        template1 = get_prompt_template()
        template2 = get_prompt_template()
        assert template1 is not template2

        builder1 = get_rag_prompt_builder()
        builder2 = get_rag_prompt_builder()
        assert builder1 is not builder2
