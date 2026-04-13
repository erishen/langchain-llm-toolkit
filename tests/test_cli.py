from typer.testing import CliRunner
from unittest.mock import patch, Mock

from cli import app

runner = CliRunner()


class TestGenerateCommand:
    """测试生成命令"""

    @patch("cli.LLMIntegration")
    def test_generate_with_defaults(self, mock_llm_class):
        """测试使用默认参数生成"""
        mock_llm = Mock()
        mock_llm.generate.return_value = "这是生成的文本"
        mock_llm_class.return_value = mock_llm

        result = runner.invoke(app, ["generate", "你好"])

        assert result.exit_code == 0
        assert "你好" in result.output
        assert "这是生成的文本" in result.output
        mock_llm.set_model.assert_called_once()
        mock_llm.set_temperature.assert_called_once()
        mock_llm.generate.assert_called_once_with("你好")

    @patch("cli.LLMIntegration")
    def test_generate_with_custom_model(self, mock_llm_class):
        """测试使用自定义模型生成"""
        mock_llm = Mock()
        mock_llm.generate.return_value = "自定义模型响应"
        mock_llm_class.return_value = mock_llm

        result = runner.invoke(app, ["generate", "测试", "--model", "gpt-4o"])

        assert result.exit_code == 0
        assert "gpt-4o" in result.output
        assert "自定义模型响应" in result.output

    @patch("cli.LLMIntegration")
    def test_generate_with_custom_temperature(self, mock_llm_class):
        """测试使用自定义温度生成"""
        mock_llm = Mock()
        mock_llm.generate.return_value = "温度响应"
        mock_llm_class.return_value = mock_llm

        result = runner.invoke(app, ["generate", "测试", "--temperature", "0.5"])

        assert result.exit_code == 0
        assert "0.5" in result.output
        mock_llm.set_temperature.assert_called_once_with(0.5)


class TestChatCommand:
    """测试聊天命令"""

    @patch("cli.ConversationManager")
    def test_chat_exit(self, mock_conv_class):
        """测试退出聊天"""
        mock_conv = Mock()
        mock_conv_class.return_value = mock_conv

        result = runner.invoke(app, ["chat"], input="exit\n")

        assert result.exit_code == 0
        assert "再见" in result.output

    @patch("cli.ConversationManager")
    def test_chat_clear_history(self, mock_conv_class):
        """测试清空历史"""
        mock_conv = Mock()
        mock_conv_class.return_value = mock_conv

        result = runner.invoke(app, ["chat"], input="clear\nexit\n")

        assert result.exit_code == 0
        assert "对话历史已清空" in result.output
        mock_conv.clear_history.assert_called_once()

    @patch("cli.ConversationManager")
    def test_chat_show_history(self, mock_conv_class):
        """测试显示历史"""
        mock_conv = Mock()
        mock_conv.get_history.return_value = [
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "你好！"},
        ]
        mock_conv_class.return_value = mock_conv

        result = runner.invoke(app, ["chat"], input="history\nexit\n")

        assert result.exit_code == 0
        assert "对话历史" in result.output

    @patch("cli.ConversationManager")
    def test_chat_conversation(self, mock_conv_class):
        """测试对话"""
        mock_conv = Mock()
        mock_conv.converse.return_value = "你好！我是AI助手。"
        mock_conv_class.return_value = mock_conv

        result = runner.invoke(app, ["chat"], input="你好\nexit\n")

        assert result.exit_code == 0
        assert "你好！我是AI助手。" in result.output
        mock_conv.converse.assert_called_once_with("你好")


class TestModelCommands:
    """测试模型命令"""

    def test_list_models(self):
        """测试列出模型"""
        result = runner.invoke(app, ["model", "list"])

        assert result.exit_code == 0
        assert "支持的模型" in result.output
        assert "OpenAI 模型" in result.output
        assert "gpt-4o" in result.output
        assert "Anthropic 模型" in result.output
        assert "claude-3-opus" in result.output
        assert "Ollama 本地模型" in result.output
        assert "ollama/llama3" in result.output

    def test_set_model(self):
        """测试设置模型"""
        result = runner.invoke(app, ["model", "set", "gpt-4o"])

        assert result.exit_code == 0
        assert "gpt-4o" in result.output
        assert "默认模型已设置" in result.output


class TestTemperatureCommands:
    """测试温度命令"""

    def test_set_temperature(self):
        """测试设置温度"""
        result = runner.invoke(app, ["temperature", "set", "0.8"])

        assert result.exit_code == 0
        assert "0.8" in result.output
        assert "温度参数已设置" in result.output

    def test_get_temperature(self):
        """测试获取温度"""
        result = runner.invoke(app, ["temperature", "get"])

        assert result.exit_code == 0
        assert "当前温度参数" in result.output


class TestCLIIntegration:
    """测试 CLI 集成"""

    @patch("cli.LLMIntegration")
    def test_full_workflow(self, mock_llm_class):
        """测试完整工作流"""
        mock_llm = Mock()
        mock_llm.generate.return_value = "工作流响应"
        mock_llm_class.return_value = mock_llm

        result = runner.invoke(app, ["generate", "测试工作流"])

        assert result.exit_code == 0
        assert "工作流响应" in result.output

    def test_help_command(self):
        """测试帮助命令"""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "LangChain LLM Toolkit 命令行工具" in result.output

    def test_generate_help(self):
        """测试生成命令帮助"""
        result = runner.invoke(app, ["generate", "--help"])

        assert result.exit_code == 0
        assert "生成文本响应" in result.output

    def test_chat_help(self):
        """测试聊天命令帮助"""
        result = runner.invoke(app, ["chat", "--help"])

        assert result.exit_code == 0
        assert "进入聊天模式" in result.output
