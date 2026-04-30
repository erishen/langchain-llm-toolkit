from unittest.mock import Mock, patch

from langchain_llm_toolkit.conversation import ConversationManager


class TestConversationManager:
    """测试对话管理器"""

    def test_init(self):
        """测试初始化"""
        manager = ConversationManager()
        assert manager.llm_integration is not None
        assert manager.history == []
        assert "helpful assistant" in manager.system_prompt.lower()

    @patch("langchain_llm_toolkit.conversation.LLMIntegration")
    def test_converse_success(self, mock_llm_class):
        """测试成功对话"""
        mock_llm = Mock()
        mock_llm.chat.return_value = "你好！我是AI助手。"
        mock_llm_class.return_value = mock_llm

        manager = ConversationManager()
        response = manager.converse("你好")

        assert response == "你好！我是AI助手。"
        assert len(manager.history) == 2
        assert manager.history[0]["role"] == "user"
        assert manager.history[0]["content"] == "你好"
        assert manager.history[1]["role"] == "assistant"
        assert manager.history[1]["content"] == "你好！我是AI助手。"

    @patch("langchain_llm_toolkit.conversation.LLMIntegration")
    def test_converse_with_context(self, mock_llm_class):
        """测试带上下文的对话"""
        mock_llm = Mock()
        mock_llm.chat.side_effect = ["你好！", "你刚才问我'你好'"]
        mock_llm_class.return_value = mock_llm

        manager = ConversationManager()

        response1 = manager.converse("你好")
        assert response1 == "你好！"
        assert len(manager.history) == 2

        response2 = manager.converse("我刚才说了什么？")
        assert response2 == "你刚才问我'你好'"
        assert len(manager.history) == 4

        mock_llm.chat.assert_called()
        last_call_args = mock_llm.chat.call_args[0][0]
        assert len(last_call_args) == 4
        assert last_call_args[0]["role"] == "system"
        assert last_call_args[1]["role"] == "user"
        assert last_call_args[2]["role"] == "assistant"
        assert last_call_args[3]["role"] == "user"

    @patch("langchain_llm_toolkit.conversation.LLMIntegration")
    def test_converse_error_handling(self, mock_llm_class):
        """测试错误处理"""
        mock_llm = Mock()
        mock_llm.chat.side_effect = Exception("API Error")
        mock_llm_class.return_value = mock_llm

        manager = ConversationManager()
        response = manager.converse("测试")

        assert "Error:" in response
        assert "API Error" in response
        assert len(manager.history) == 0

    def test_get_history(self):
        """测试获取历史"""
        manager = ConversationManager()
        manager.history = [
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "你好！"},
        ]

        history = manager.get_history()
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "assistant"

    def test_clear_history(self):
        """测试清空历史"""
        manager = ConversationManager()
        manager.history = [
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "你好！"},
        ]

        manager.clear_history()
        assert manager.history == []

    @patch("langchain_llm_toolkit.conversation.LLMIntegration")
    def test_set_model(self, mock_llm_class):
        """测试设置模型"""
        mock_llm = Mock()
        mock_llm_class.return_value = mock_llm

        manager = ConversationManager()
        manager.set_model("gpt-4o")

        mock_llm.set_model.assert_called_once_with("gpt-4o")

    @patch("langchain_llm_toolkit.conversation.LLMIntegration")
    def test_set_temperature(self, mock_llm_class):
        """测试设置温度"""
        mock_llm = Mock()
        mock_llm_class.return_value = mock_llm

        manager = ConversationManager()
        manager.set_temperature(0.5)

        mock_llm.set_temperature.assert_called_once_with(0.5)

    @patch("langchain_llm_toolkit.conversation.LLMIntegration")
    def test_multiple_conversations(self, mock_llm_class):
        """测试多轮对话"""
        mock_llm = Mock()
        mock_llm.chat.side_effect = ["回复1", "回复2", "回复3"]
        mock_llm_class.return_value = mock_llm

        manager = ConversationManager()

        responses = []
        for i in range(3):
            response = manager.converse(f"问题{i + 1}")
            responses.append(response)

        assert responses == ["回复1", "回复2", "回复3"]
        assert len(manager.history) == 6

    @patch("langchain_llm_toolkit.conversation.LLMIntegration")
    def test_history_persistence(self, mock_llm_class):
        """测试历史持久化"""
        mock_llm = Mock()
        mock_llm.chat.return_value = "回复"
        mock_llm_class.return_value = mock_llm

        manager = ConversationManager()
        manager.converse("问题1")
        manager.converse("问题2")

        history = manager.get_history()
        assert len(history) == 4

        manager.clear_history()
        assert len(manager.get_history()) == 0

        manager.converse("新问题")
        assert len(manager.get_history()) == 2

    @patch("langchain_llm_toolkit.conversation.LLMIntegration")
    def test_converse_with_long_input(self, mock_llm_class):
        """测试长输入对话"""
        mock_llm = Mock()
        mock_llm.chat.return_value = "长回复"
        mock_llm_class.return_value = mock_llm

        manager = ConversationManager()
        long_input = "这是一个很长的问题" * 100
        response = manager.converse(long_input)

        assert response == "长回复"
        assert manager.history[0]["content"] == long_input

    @patch("langchain_llm_toolkit.conversation.LLMIntegration")
    def test_converse_with_special_characters(self, mock_llm_class):
        """测试包含特殊字符的对话"""
        mock_llm = Mock()
        mock_llm.chat.return_value = "特殊字符回复"
        mock_llm_class.return_value = mock_llm

        manager = ConversationManager()
        special_input = "特殊字符: \n\t\r\"'<>&"
        response = manager.converse(special_input)

        assert response == "特殊字符回复"
        assert manager.history[0]["content"] == special_input

    @patch("langchain_llm_toolkit.conversation.LLMIntegration")
    def test_converse_with_unicode(self, mock_llm_class):
        """测试包含 Unicode 字符的对话"""
        mock_llm = Mock()
        mock_llm.chat.return_value = "Unicode 回复 😀"
        mock_llm_class.return_value = mock_llm

        manager = ConversationManager()
        unicode_input = "Unicode 测试: 中文 日本語 한국어 😀 🎉"
        response = manager.converse(unicode_input)

        assert response == "Unicode 回复 😀"
        assert manager.history[0]["content"] == unicode_input

    @patch("langchain_llm_toolkit.conversation.LLMIntegration")
    def test_converse_with_code_snippet(self, mock_llm_class):
        """测试包含代码片段的对话"""
        mock_llm = Mock()
        mock_llm.chat.return_value = "代码解释"
        mock_llm_class.return_value = mock_llm

        manager = ConversationManager()
        code_input = """
```python
def hello():
    print("Hello, World!")
```
"""
        response = manager.converse(code_input)

        assert response == "代码解释"
        assert "```python" in manager.history[0]["content"]

    @patch("langchain_llm_toolkit.conversation.LLMIntegration")
    def test_converse_with_markdown(self, mock_llm_class):
        """测试包含 Markdown 的对话"""
        mock_llm = Mock()
        mock_llm.chat.return_value = "**Markdown** 回复"
        mock_llm_class.return_value = mock_llm

        manager = ConversationManager()
        markdown_input = "# 标题\n\n**粗体** 和 *斜体*\n\n- 列表项"
        response = manager.converse(markdown_input)

        assert response == "**Markdown** 回复"
        assert "# 标题" in manager.history[0]["content"]

    @patch("langchain_llm_toolkit.conversation.LLMIntegration")
    def test_converse_empty_input(self, mock_llm_class):
        """测试空输入"""
        mock_llm = Mock()
        mock_llm.chat.side_effect = ValueError("Empty input")
        mock_llm_class.return_value = mock_llm

        manager = ConversationManager()
        response = manager.converse("")

        assert "Error:" in response
        assert len(manager.history) == 0

    @patch("langchain_llm_toolkit.conversation.LLMIntegration")
    def test_converse_whitespace_input(self, mock_llm_class):
        """测试空白输入"""
        mock_llm = Mock()
        mock_llm.chat.side_effect = ValueError("Whitespace input")
        mock_llm_class.return_value = mock_llm

        manager = ConversationManager()
        response = manager.converse("   \n\t  ")

        assert "Error:" in response
        assert len(manager.history) == 0

    @patch("langchain_llm_toolkit.conversation.LLMIntegration")
    def test_multiple_managers_independent(self, mock_llm_class):
        """测试多个管理器相互独立"""
        mock_llm = Mock()
        mock_llm.chat.side_effect = ["回复1", "回复2"]
        mock_llm_class.return_value = mock_llm

        manager1 = ConversationManager()
        manager2 = ConversationManager()

        response1 = manager1.converse("问题1")
        response2 = manager2.converse("问题2")

        assert response1 == "回复1"
        assert response2 == "回复2"
        assert len(manager1.history) == 2
        assert len(manager2.history) == 2
        assert manager1.history[0]["content"] == "问题1"
        assert manager2.history[0]["content"] == "问题2"

    @patch("langchain_llm_toolkit.conversation.LLMIntegration")
    def test_converse_after_clear(self, mock_llm_class):
        """测试清空历史后的对话"""
        mock_llm = Mock()
        mock_llm.chat.side_effect = ["回复1", "回复2", "回复3"]
        mock_llm_class.return_value = mock_llm

        manager = ConversationManager()

        manager.converse("问题1")
        manager.converse("问题2")
        assert len(manager.history) == 4

        manager.clear_history()
        assert len(manager.history) == 0

        manager.converse("问题3")
        assert len(manager.history) == 2
        assert manager.history[0]["content"] == "问题3"

    @patch("langchain_llm_toolkit.conversation.LLMIntegration")
    def test_converse_with_system_prompt(self, mock_llm_class):
        """测试系统提示词"""
        mock_llm = Mock()
        mock_llm.chat.return_value = "回复"
        mock_llm_class.return_value = mock_llm

        manager = ConversationManager()
        manager.converse("问题")

        call_args = mock_llm.chat.call_args[0][0]
        assert call_args[0]["role"] == "system"
        assert "helpful assistant" in call_args[0]["content"].lower()

    @patch("langchain_llm_toolkit.conversation.LLMIntegration")
    def test_converse_preserves_order(self, mock_llm_class):
        """测试对话顺序保持"""
        mock_llm = Mock()
        mock_llm.chat.side_effect = ["回复1", "回复2", "回复3"]
        mock_llm_class.return_value = mock_llm

        manager = ConversationManager()

        questions = ["问题1", "问题2", "问题3"]
        for q in questions:
            manager.converse(q)

        assert len(manager.history) == 6
        for i, q in enumerate(questions):
            assert manager.history[i * 2]["content"] == q
            assert manager.history[i * 2]["role"] == "user"
            assert manager.history[i * 2 + 1]["role"] == "assistant"

    @patch("langchain_llm_toolkit.conversation.LLMIntegration")
    def test_converse_with_different_models(self, mock_llm_class):
        """测试切换模型"""
        mock_llm = Mock()
        mock_llm.chat.return_value = "回复"
        mock_llm_class.return_value = mock_llm

        manager = ConversationManager()

        manager.set_model("gpt-4o")
        manager.converse("问题1")

        mock_llm.set_model.assert_called_with("gpt-4o")

        manager.set_model("gpt-3.5-turbo")
        manager.converse("问题2")

        mock_llm.set_model.assert_called_with("gpt-3.5-turbo")

    @patch("langchain_llm_toolkit.conversation.LLMIntegration")
    def test_converse_with_different_temperatures(self, mock_llm_class):
        """测试切换温度"""
        mock_llm = Mock()
        mock_llm.chat.return_value = "回复"
        mock_llm_class.return_value = mock_llm

        manager = ConversationManager()

        manager.set_temperature(0.5)
        manager.converse("问题1")

        mock_llm.set_temperature.assert_called_with(0.5)

        manager.set_temperature(1.0)
        manager.converse("问题2")

        mock_llm.set_temperature.assert_called_with(1.0)

    @patch("langchain_llm_toolkit.conversation.LLMIntegration")
    def test_converse_network_error(self, mock_llm_class):
        """测试网络错误"""
        mock_llm = Mock()
        mock_llm.chat.side_effect = ConnectionError("Network error")
        mock_llm_class.return_value = mock_llm

        manager = ConversationManager()
        response = manager.converse("问题")

        assert "Error:" in response
        assert "Network error" in response
        assert len(manager.history) == 0

    @patch("langchain_llm_toolkit.conversation.LLMIntegration")
    def test_converse_timeout_error(self, mock_llm_class):
        """测试超时错误"""
        mock_llm = Mock()
        mock_llm.chat.side_effect = TimeoutError("Request timeout")
        mock_llm_class.return_value = mock_llm

        manager = ConversationManager()
        response = manager.converse("问题")

        assert "Error:" in response
        assert "Request timeout" in response
        assert len(manager.history) == 0

    @patch("langchain_llm_toolkit.conversation.LLMIntegration")
    def test_converse_rate_limit_error(self, mock_llm_class):
        """测试速率限制错误"""
        mock_llm = Mock()
        mock_llm.chat.side_effect = Exception("Rate limit exceeded")
        mock_llm_class.return_value = mock_llm

        manager = ConversationManager()
        response = manager.converse("问题")

        assert "Error:" in response
        assert "Rate limit exceeded" in response
        assert len(manager.history) == 0

    @patch("langchain_llm_toolkit.conversation.LLMIntegration")
    def test_get_history_returns_reference(self, mock_llm_class):
        """测试获取历史返回引用"""
        mock_llm = Mock()
        mock_llm.chat.return_value = "回复"
        mock_llm_class.return_value = mock_llm

        manager = ConversationManager()
        manager.converse("问题")

        history1 = manager.get_history()
        history2 = manager.get_history()

        assert history1 == history2
        assert history1 is history2
