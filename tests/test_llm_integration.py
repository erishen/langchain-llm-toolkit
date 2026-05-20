import unittest
from unittest.mock import MagicMock, patch

from langchain_llm_toolkit.llm_integration import LLMIntegration


class TestLLMIntegration(unittest.TestCase):
    def setUp(self):
        self.llm = LLMIntegration()

    @patch("requests.post")
    def test_generate_success_ollama(self, mock_post):
        """测试成功生成文本（Ollama）"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"response": "测试响应"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        self.llm.set_model("ollama/gemma3")

        prompt = "Hello, who are you?"
        response = self.llm.generate(prompt)

        self.assertEqual(response, "测试响应")
        mock_post.assert_called_once()

    @patch("requests.post")
    def test_generate_error_ollama(self, mock_post):
        """测试生成文本时出错"""
        mock_post.side_effect = Exception("API 错误")

        self.llm.set_model("ollama/gemma3")

        prompt = "Hello, who are you?"
        with self.assertRaises(Exception):
            self.llm.generate(prompt)

    @patch("litellm.completion")
    def test_generate_success_litellm(self, mock_completion):
        """测试成功生成文本（LiteLLM）"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(text="测试响应")]
        mock_completion.return_value = mock_response

        self.llm.set_model("gpt-4o")

        prompt = "Hello, who are you?"
        response = self.llm.generate(prompt)

        self.assertEqual(response, "测试响应")
        mock_completion.assert_called_once()

    @patch("litellm.completion")
    def test_generate_error_litellm(self, mock_completion):
        """测试生成文本时出错"""
        mock_completion.side_effect = Exception("API 错误")

        self.llm.set_model("gpt-4o")

        prompt = "Hello, who are you?"
        with self.assertRaises(Exception):
            self.llm.generate(prompt)

    @patch("requests.post")
    def test_chat_success_ollama(self, mock_post):
        """测试成功聊天（Ollama）"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"message": {"content": "聊天响应"}}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        self.llm.set_model("ollama/gemma3")

        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What's the capital of France?"},
        ]
        response = self.llm.chat(messages)

        self.assertEqual(response, "聊天响应")
        mock_post.assert_called_once()

    @patch("requests.post")
    def test_chat_error_ollama(self, mock_post):
        """测试聊天时出错（Ollama）"""
        mock_post.side_effect = Exception("API 错误")

        self.llm.set_model("ollama/gemma3")

        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What's the capital of France?"},
        ]
        response = self.llm.chat(messages)

        self.assertIn("Error", response)
        self.assertIn("API 错误", response)

    def test_set_model(self):
        """测试设置模型"""
        new_model = "gpt-4"
        self.llm.set_model(new_model)
        self.assertEqual(self.llm.model, new_model)

    def test_set_temperature(self):
        """测试设置温度参数"""
        new_temperature = 0.7
        self.llm.set_temperature(new_temperature)
        self.assertEqual(self.llm.temperature, new_temperature)

    def test_set_temperature_invalid(self):
        """测试设置无效温度参数"""
        with self.assertRaises(ValueError):
            self.llm.set_temperature(3.0)

    def test_set_timeout(self):
        """测试设置超时时间"""
        new_timeout = 60
        self.llm.set_timeout(new_timeout)
        self.assertEqual(self.llm.timeout, new_timeout)

    def test_set_timeout_invalid(self):
        """测试设置无效超时时间"""
        with self.assertRaises(ValueError):
            self.llm.set_timeout(-1)

    def test_validate_prompt_empty(self):
        """测试验证空提示"""
        with self.assertRaises(ValueError):
            self.llm._validate_prompt("")

    def test_validate_prompt_too_long(self):
        """测试验证过长提示"""
        long_prompt = "a" * 10001
        with self.assertRaises(ValueError):
            self.llm._validate_prompt(long_prompt)

    def test_validate_messages_empty(self):
        """测试验证空消息列表"""
        with self.assertRaises(ValueError):
            self.llm._validate_messages([])

    def test_validate_messages_invalid_format(self):
        """测试验证无效消息格式"""
        with self.assertRaises(ValueError):
            self.llm._validate_messages([{"role": "user"}])

    @patch("requests.post")
    def test_generate_stream_ollama(self, mock_post):
        """测试流式生成（Ollama）"""
        import json

        # 模拟流式响应
        mock_response = MagicMock()
        mock_response.iter_lines.return_value = [
            json.dumps({"response": "Hello"}).encode(),
            json.dumps({"response": " world"}).encode(),
            json.dumps({"response": "!"}).encode(),
        ]
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        self.llm.set_model("ollama/gemma3")

        chunks = list(self.llm.generate_stream("Test"))
        self.assertEqual(chunks, ["Hello", " world", "!"])

    @patch("langchain_llm_toolkit.llm_integration.LLMIntegration.generate")
    def test_generate_stream_non_ollama(self, mock_generate):
        """测试非 Ollama 模型的流式生成（应回退到普通生成）"""
        mock_generate.return_value = "普通响应"

        self.llm.set_model("gpt-4o")

        chunks = list(self.llm.generate_stream("Test"))
        self.assertEqual(chunks, ["普通响应"])

    @patch("requests.post")
    def test_generate_stream_error(self, mock_post):
        """测试流式生成时出错"""
        mock_post.side_effect = Exception("Stream Error")

        self.llm.set_model("ollama/gemma3")

        chunks = list(self.llm.generate_stream("Test"))
        self.assertEqual(len(chunks), 1)
        self.assertIn("Error", chunks[0])
        self.assertIn("Stream Error", chunks[0])

    @patch("litellm.completion")
    def test_chat_success_litellm(self, mock_completion):
        """测试成功聊天（LiteLLM）"""
        mock_response = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "聊天响应"
        mock_response.choices = [MagicMock(message=mock_message)]
        mock_completion.return_value = mock_response

        self.llm.set_model("gpt-4o")

        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What's the capital of France?"},
        ]
        response = self.llm.chat(messages)

        self.assertEqual(response, "聊天响应")
        mock_completion.assert_called_once()

    @patch("litellm.completion")
    def test_chat_error_litellm(self, mock_completion):
        """测试聊天时出错（LiteLLM）"""
        mock_completion.side_effect = Exception("API 错误")

        self.llm.set_model("gpt-4o")

        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What's the capital of France?"},
        ]
        response = self.llm.chat(messages)

        self.assertIn("Error", response)
        self.assertIn("API 错误", response)

    def test_validate_messages_not_dict(self):
        """测试验证非字典类型的消息"""
        with self.assertRaises(ValueError):
            self.llm._validate_messages(["not a dict"])

    def test_validate_messages_empty_content(self):
        """测试验证空内容的消息"""
        with self.assertRaises(ValueError):
            self.llm._validate_messages([{"role": "user", "content": ""}])

    def test_validate_messages_whitespace_content(self):
        """测试验证只有空白的消息内容"""
        with self.assertRaises(ValueError):
            self.llm._validate_messages([{"role": "user", "content": "   "}])

    def test_validate_prompt_whitespace(self):
        """测试验证只有空白的提示"""
        with self.assertRaises(ValueError):
            self.llm._validate_prompt("   ")

    @patch("litellm.completion")
    def test_generate_litellm_with_message_content(self, mock_completion):
        """测试 LiteLLM 响应包含 message.content"""
        mock_response = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "消息内容响应"
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        del mock_choice.text
        mock_response.choices = [mock_choice]
        mock_completion.return_value = mock_response

        self.llm.set_model("gpt-4o")
        response = self.llm.generate("Test")

        self.assertEqual(response, "消息内容响应")

    @patch("litellm.completion")
    def test_generate_litellm_unexpected_format(self, mock_completion):
        """测试 LiteLLM 意外的响应格式"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        del mock_response.choices[0].text
        del mock_response.choices[0].message
        mock_completion.return_value = mock_response

        self.llm.set_model("gpt-4o")
        response = self.llm.generate("Test")

        self.assertIn("Error", response)
        self.assertIn("Unexpected response format", response)

    @patch("requests.post")
    def test_generate_ollama_with_custom_timeout(self, mock_post):
        """测试 Ollama 使用自定义超时"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"response": "测试响应"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        self.llm.set_model("ollama/gemma3")
        response = self.llm.generate("Test", timeout=60)

        self.assertEqual(response, "测试响应")
        call_args = mock_post.call_args
        self.assertEqual(call_args[1]["timeout"], 60)

    @patch("litellm.completion")
    def test_generate_litellm_with_custom_timeout(self, mock_completion):
        """测试 LiteLLM 使用自定义超时"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(text="测试响应")]
        mock_completion.return_value = mock_response

        self.llm.set_model("gpt-4o")
        response = self.llm.generate("Test", timeout=60)

        self.assertEqual(response, "测试响应")
        call_args = mock_completion.call_args
        self.assertEqual(call_args[1]["timeout"], 60)

    @patch("requests.post")
    def test_chat_ollama_with_custom_timeout(self, mock_post):
        """测试 Ollama chat 使用自定义超时"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"message": {"content": "聊天响应"}}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        self.llm.set_model("ollama/gemma3")
        messages = [{"role": "user", "content": "Test"}]
        response = self.llm.chat(messages, timeout=60)

        self.assertEqual(response, "聊天响应")
        call_args = mock_post.call_args
        self.assertEqual(call_args[1]["timeout"], 60)

    @patch("litellm.completion")
    def test_chat_litellm_with_custom_timeout(self, mock_completion):
        """测试 LiteLLM chat 使用自定义超时"""
        mock_response = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "聊天响应"
        mock_response.choices = [MagicMock(message=mock_message)]
        mock_completion.return_value = mock_response

        self.llm.set_model("gpt-4o")
        messages = [{"role": "user", "content": "Test"}]
        response = self.llm.chat(messages, timeout=60)

        self.assertEqual(response, "聊天响应")
        call_args = mock_completion.call_args
        self.assertEqual(call_args[1]["timeout"], 60)

    def test_init_with_custom_params(self):
        """测试使用自定义参数初始化"""
        llm = LLMIntegration(timeout=60, max_retries=5)
        self.assertEqual(llm.timeout, 60)
        self.assertEqual(llm.max_retries, 5)

    @patch("requests.post")
    def test_generate_ollama_empty_response(self, mock_post):
        """测试 Ollama 返回空响应"""
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        self.llm.set_model("ollama/gemma3")
        response = self.llm.generate("Test")

        self.assertEqual(response, "")

    @patch("requests.post")
    def test_chat_ollama_empty_response(self, mock_post):
        """测试 Ollama chat 返回空响应"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"message": {}}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        self.llm.set_model("ollama/gemma3")
        messages = [{"role": "user", "content": "Test"}]
        response = self.llm.chat(messages)

        self.assertEqual(response, "")

    @patch("litellm.completion")
    def test_generate_litellm_empty_text(self, mock_completion):
        """测试 LiteLLM 返回空文本"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(text=None)]
        mock_completion.return_value = mock_response

        self.llm.set_model("gpt-4o")
        response = self.llm.generate("Test")

        self.assertEqual(response, "")

    @patch("litellm.completion")
    def test_chat_litellm_empty_content(self, mock_completion):
        """测试 LiteLLM chat 返回空内容"""
        mock_response = MagicMock()
        mock_message = MagicMock()
        mock_message.content = None
        mock_response.choices = [MagicMock(message=mock_message)]
        mock_completion.return_value = mock_response

        self.llm.set_model("gpt-4o")
        messages = [{"role": "user", "content": "Test"}]
        response = self.llm.chat(messages)

        self.assertEqual(response, "")

    @patch("requests.post")
    def test_generate_stream_with_empty_lines(self, mock_post):
        """测试流式生成包含空行"""
        import json

        mock_response = MagicMock()
        mock_response.iter_lines.return_value = [
            None,
            json.dumps({"response": "Hello"}).encode(),
            None,
            json.dumps({"response": " world"}).encode(),
            None,
        ]
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        self.llm.set_model("ollama/gemma3")
        chunks = list(self.llm.generate_stream("Test"))

        self.assertEqual(chunks, ["Hello", " world"])


if __name__ == "__main__":
    unittest.main()
