import os
import tempfile
from unittest.mock import Mock

import pytest

from langchain_llm_toolkit.conversation_store import (
    Conversation,
    ConversationManagerWithPersistence,
    ConversationStore,
    Message,
)


class TestMessage:
    """测试消息数据类"""

    def test_create_message(self):
        """测试创建消息"""
        msg = Message(
            role="user",
            content="你好",
            timestamp="2024-01-01T00:00:00",
        )

        assert msg.role == "user"
        assert msg.content == "你好"
        assert msg.metadata is None

    def test_message_to_dict(self):
        """测试消息转字典"""
        msg = Message(
            role="assistant",
            content="你好！",
            timestamp="2024-01-01T00:00:00",
            metadata={"model": "gpt-4"},
        )

        data = msg.to_dict()

        assert data["role"] == "assistant"
        assert data["content"] == "你好！"
        assert data["metadata"]["model"] == "gpt-4"

    def test_message_from_dict(self):
        """测试从字典创建消息"""
        data = {
            "role": "user",
            "content": "测试",
            "timestamp": "2024-01-01T00:00:00",
            "metadata": {"key": "value"},
        }

        msg = Message.from_dict(data)

        assert msg.role == "user"
        assert msg.content == "测试"
        assert msg.metadata == {"key": "value"}


class TestConversation:
    """测试对话数据类"""

    @pytest.fixture
    def sample_conversation(self):
        return Conversation(
            id="test-conv-1",
            title="测试对话",
            messages=[
                Message(role="user", content="你好", timestamp="2024-01-01T00:00:00"),
                Message(role="assistant", content="你好！", timestamp="2024-01-01T00:00:01"),
            ],
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:01",
        )

    def test_create_conversation(self, sample_conversation):
        """测试创建对话"""
        assert sample_conversation.id == "test-conv-1"
        assert sample_conversation.title == "测试对话"
        assert len(sample_conversation.messages) == 2

    def test_conversation_to_dict(self, sample_conversation):
        """测试对话转字典"""
        data = sample_conversation.to_dict()

        assert data["id"] == "test-conv-1"
        assert data["title"] == "测试对话"
        assert len(data["messages"]) == 2

    def test_conversation_from_dict(self):
        """测试从字典创建对话"""
        data = {
            "id": "conv-1",
            "title": "新对话",
            "messages": [
                {"role": "user", "content": "测试", "timestamp": "2024-01-01T00:00:00"},
            ],
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }

        conv = Conversation.from_dict(data)

        assert conv.id == "conv-1"
        assert len(conv.messages) == 1


class TestConversationStore:
    """测试对话存储"""

    @pytest.fixture
    def temp_db(self):
        """创建临时数据库"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        yield db_path
        os.unlink(db_path)

    @pytest.fixture
    def store(self, temp_db):
        return ConversationStore(db_path=temp_db)

    @pytest.fixture
    def sample_conversation(self):
        return Conversation(
            id="conv-1",
            title="测试对话",
            messages=[
                Message(role="user", content="你好", timestamp="2024-01-01T00:00:00"),
            ],
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
        )

    def test_save_conversation(self, store, sample_conversation):
        """测试保存对话"""
        result = store.save_conversation(sample_conversation)
        assert result is True

    def test_get_conversation(self, store, sample_conversation):
        """测试获取对话"""
        store.save_conversation(sample_conversation)

        conv = store.get_conversation("conv-1")

        assert conv is not None
        assert conv.id == "conv-1"
        assert conv.title == "测试对话"

    def test_get_nonexistent_conversation(self, store):
        """测试获取不存在的对话"""
        conv = store.get_conversation("nonexistent")
        assert conv is None

    def test_list_conversations(self, store):
        """测试列出对话"""
        for i in range(3):
            conv = Conversation(
                id=f"conv-{i}",
                title=f"对话 {i}",
                messages=[],
                created_at=f"2024-01-0{i}T00:00:00",
                updated_at=f"2024-01-0{i}T00:00:00",
            )
            store.save_conversation(conv)

        conversations = store.list_conversations(limit=10)

        assert len(conversations) == 3

    def test_list_conversations_pagination(self, store):
        """测试分页"""
        for i in range(5):
            conv = Conversation(
                id=f"conv-{i}",
                title=f"对话 {i}",
                messages=[],
                created_at=f"2024-01-0{i}T00:00:00",
                updated_at=f"2024-01-0{i}T00:00:00",
            )
            store.save_conversation(conv)

        page1 = store.list_conversations(limit=2, offset=0)
        page2 = store.list_conversations(limit=2, offset=2)

        assert len(page1) == 2
        assert len(page2) == 2

    def test_delete_conversation(self, store, sample_conversation):
        """测试删除对话"""
        store.save_conversation(sample_conversation)

        result = store.delete_conversation("conv-1")
        assert result is True

        conv = store.get_conversation("conv-1")
        assert conv is None

    def test_search_conversations(self, store):
        """测试搜索对话"""
        conv = Conversation(
            id="conv-1",
            title="Python 编程",
            messages=[
                Message(
                    role="user",
                    content="如何学习 Python？",
                    timestamp="2024-01-01T00:00:00",
                ),
            ],
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
        )
        store.save_conversation(conv)

        results = store.search_conversations("Python")

        assert len(results) >= 1

    def test_get_stats(self, store, sample_conversation):
        """测试统计信息"""
        store.save_conversation(sample_conversation)

        stats = store.get_stats()

        assert stats["total_conversations"] == 1
        assert stats["total_messages"] == 1

    def test_update_conversation(self, store, sample_conversation):
        """测试更新对话"""
        store.save_conversation(sample_conversation)

        sample_conversation.messages.append(
            Message(role="assistant", content="你好！", timestamp="2024-01-01T00:00:01")
        )
        sample_conversation.updated_at = "2024-01-01T00:00:01"
        store.save_conversation(sample_conversation)

        conv = store.get_conversation("conv-1")
        assert len(conv.messages) == 2


class TestConversationManagerWithPersistence:
    """测试带持久化的对话管理器"""

    @pytest.fixture
    def temp_db(self):
        """创建临时数据库"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        yield db_path
        os.unlink(db_path)

    @pytest.fixture
    def mock_llm(self):
        llm = Mock()
        llm.chat.return_value = "这是 AI 的回复"
        return llm

    @pytest.fixture
    def manager(self, temp_db, mock_llm):
        store = ConversationStore(db_path=temp_db)
        return ConversationManagerWithPersistence(
            llm_integration=mock_llm,
            store=store,
        )

    def test_create_conversation(self, manager):
        """测试创建对话"""
        conv = manager.create_conversation(title="新对话")

        assert conv.id is not None
        assert conv.title == "新对话"
        assert manager.current_conversation == conv

    def test_load_conversation(self, manager):
        """测试加载对话"""
        conv = manager.create_conversation(title="测试")
        conv_id = conv.id

        manager.current_conversation = None
        loaded = manager.load_conversation(conv_id)

        assert loaded is not None
        assert loaded.id == conv_id
        assert manager.current_conversation == loaded

    def test_add_message(self, manager):
        """测试添加消息"""
        manager.create_conversation()
        msg = manager.add_message("user", "你好")

        assert msg.role == "user"
        assert msg.content == "你好"
        assert len(manager.current_conversation.messages) == 1

    def test_converse(self, manager, mock_llm):
        """测试对话"""
        manager.create_conversation()
        response = manager.converse("你好")

        assert response == "这是 AI 的回复"
        mock_llm.chat.assert_called_once()
        assert len(manager.current_conversation.messages) == 2

    def test_get_history(self, manager):
        """测试获取历史"""
        manager.create_conversation()
        manager.add_message("user", "问题")
        manager.add_message("assistant", "回答")

        history = manager.get_history()

        assert len(history) == 2
        assert history[0]["role"] == "user"

    def test_clear_history(self, manager):
        """测试清空历史"""
        manager.create_conversation()
        manager.add_message("user", "问题")
        manager.clear_history()

        assert len(manager.current_conversation.messages) == 0

    def test_list_conversations(self, manager):
        """测试列出对话"""
        manager.create_conversation("对话1")
        manager.create_conversation("对话2")

        conversations = manager.list_conversations()

        assert len(conversations) >= 2

    def test_delete_conversation(self, manager):
        """测试删除对话"""
        conv = manager.create_conversation()
        conv_id = conv.id

        manager.delete_conversation(conv_id)

        assert manager.current_conversation is None

    def test_search_conversations(self, manager):
        """测试搜索对话"""
        manager.create_conversation("Python 学习")

        results = manager.search_conversations("Python")

        assert len(results) >= 1

    def test_get_stats(self, manager):
        """测试统计"""
        manager.create_conversation()
        manager.add_message("user", "测试")

        stats = manager.get_stats()

        assert stats["total_conversations"] >= 1
        assert stats["total_messages"] >= 1

    def test_auto_title_from_first_message(self, manager):
        """测试自动标题 - 第二条用户消息时更新标题"""
        manager.create_conversation()
        manager.add_message("user", "这是一个很长的问题，用于测试自动标题生成功能")

        assert manager.current_conversation.title == "新对话"
