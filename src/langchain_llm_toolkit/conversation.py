import logging

from langchain_llm_toolkit.llm_integration import LLMIntegration

logger = logging.getLogger(__name__)


class ConversationManager:
    def __init__(self):
        self.llm_integration: LLMIntegration = LLMIntegration()
        self.history = []
        self.system_prompt = (
            "You are a helpful assistant. "
            "Maintain context and respond appropriately to the user's queries."
        )

    def converse(self, user_input: str) -> str:
        """进行对话"""
        try:
            # 构建消息列表
            messages = [{"role": "system", "content": self.system_prompt}]
            messages.extend(self.history)
            messages.append({"role": "user", "content": user_input})

            # 调用LLM
            response = self.llm_integration.chat(messages)

            # 更新历史
            self.history.append({"role": "user", "content": user_input})
            self.history.append({"role": "assistant", "content": response})

            return response
        except Exception as e:
            return f"Error: {e!s}"

    def get_history(self):
        """获取对话历史"""
        return self.history

    def clear_history(self):
        """清空对话历史"""
        self.history = []

    def set_model(self, model: str):
        """设置模型"""
        self.llm_integration.set_model(model)

    def set_temperature(self, temperature: float):
        """设置温度参数"""
        self.llm_integration.set_temperature(temperature)


# 测试函数
def test_conversation():
    logger.info("Testing Conversation Manager...")
    logger.info("Note: You need to set OPENAI_API_KEY in .env file for actual API calls")

    conversation_manager = ConversationManager()

    logger.info("\n1. Testing basic conversation:")
    user_input1 = "Hello, what's your name?"
    response1 = conversation_manager.converse(user_input1)
    logger.info(f"User: {user_input1}")
    logger.info(f"Assistant: {response1}")

    logger.info("\n2. Testing context memory:")
    user_input2 = "What did I just ask you?"
    response2 = conversation_manager.converse(user_input2)
    logger.info(f"User: {user_input2}")
    logger.info(f"Assistant: {response2}")

    logger.info("\n3. Testing multi-turn conversation:")
    user_input3 = "Tell me a short story about a cat"
    response3 = conversation_manager.converse(user_input3)
    logger.info(f"User: {user_input3}")
    logger.info(f"Assistant: {response3}")

    user_input4 = "What was the story about?"
    response4 = conversation_manager.converse(user_input4)
    logger.info(f"User: {user_input4}")
    logger.info(f"Assistant: {response4}")

    logger.info("\n4. Testing history clearing:")
    conversation_manager.clear_history()
    user_input5 = "Do you remember the story?"
    response5 = conversation_manager.converse(user_input5)
    logger.info(f"User: {user_input5}")
    logger.info(f"Assistant: {response5}")

    logger.info("\n5. Testing history retrieval:")
    history = conversation_manager.get_history()
    logger.info("Conversation history:")
    for msg in history:
        logger.info(f"{msg['role']}: {msg['content'][:50]}...")

    logger.info("\nTesting completed!")


if __name__ == "__main__":
    test_conversation()
