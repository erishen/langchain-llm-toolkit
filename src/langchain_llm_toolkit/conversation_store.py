import json
import os
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class Message:
    """消息数据类"""

    role: str
    content: str
    timestamp: str
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Message":
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=data["timestamp"],
            metadata=data.get("metadata"),
        )


@dataclass
class Conversation:
    """对话数据类"""

    id: str
    title: str
    messages: list[Message]
    created_at: str
    updated_at: str
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "messages": [m.to_dict() for m in self.messages],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Conversation":
        return cls(
            id=data["id"],
            title=data["title"],
            messages=[Message.from_dict(m) for m in data["messages"]],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            metadata=data.get("metadata"),
        )


class ConversationStore:
    """对话历史持久化存储

    使用 SQLite 存储对话历史。
    """

    def __init__(self, db_path: str | None = None):
        """
        初始化对话存储

        Args:
            db_path: 数据库路径（默认从环境变量读取）
        """
        self.db_path = db_path or os.environ.get("CONVERSATION_DB_PATH", "./data/conversations.db")
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    @contextmanager
    def _get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        """初始化数据库表"""
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    messages TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    metadata TEXT
                )
            """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_created_at ON conversations(created_at)
            """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_updated_at ON conversations(updated_at)
            """
            )
            conn.commit()

    def save_conversation(self, conversation: Conversation) -> bool:
        """保存对话"""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO conversations
                (id, title, messages, created_at, updated_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    conversation.id,
                    conversation.title,
                    json.dumps([m.to_dict() for m in conversation.messages]),
                    conversation.created_at,
                    conversation.updated_at,
                    json.dumps(conversation.metadata) if conversation.metadata else None,
                ),
            )
            conn.commit()
        return True

    def get_conversation(self, conversation_id: str) -> Conversation | None:
        """获取对话"""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM conversations WHERE id = ?", (conversation_id,)
            ).fetchone()

            if row:
                return Conversation(
                    id=row["id"],
                    title=row["title"],
                    messages=[Message.from_dict(m) for m in json.loads(row["messages"])],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    metadata=json.loads(row["metadata"]) if row["metadata"] else None,
                )
        return None

    def list_conversations(
        self,
        limit: int = 20,
        offset: int = 0,
        order_by: str = "updated_at",
        descending: bool = True,
    ) -> list[Conversation]:
        """列出对话"""
        order = "DESC" if descending else "ASC"
        with self._get_connection() as conn:
            rows = conn.execute(
                f"""
                SELECT * FROM conversations
                ORDER BY {order_by} {order}
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            ).fetchall()

            conversations = [
                Conversation(
                    id=row["id"],
                    title=row["title"],
                    messages=[Message.from_dict(m) for m in json.loads(row["messages"])],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    metadata=json.loads(row["metadata"]) if row["metadata"] else None,
                )
                for row in rows
            ]
        return conversations

    def delete_conversation(self, conversation_id: str) -> bool:
        """删除对话"""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
            conn.commit()
        return True

    def search_conversations(self, query: str, limit: int = 10) -> list[Conversation]:
        """搜索对话"""
        with self._get_connection() as conn:
            rows = conn.execute(
                """
                SELECT * FROM conversations
                WHERE title LIKE ? OR messages LIKE ?
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (f"%{query}%", f"%{query}%", limit),
            ).fetchall()

            conversations = [
                Conversation(
                    id=row["id"],
                    title=row["title"],
                    messages=[Message.from_dict(m) for m in json.loads(row["messages"])],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    metadata=json.loads(row["metadata"]) if row["metadata"] else None,
                )
                for row in rows
            ]
        return conversations

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        with self._get_connection() as conn:
            total = conn.execute("SELECT COUNT(*) FROM conversations").fetchone()[0]
            total_messages = 0
            rows = conn.execute("SELECT messages FROM conversations").fetchall()
            for row in rows:
                messages = json.loads(row["messages"])
                total_messages += len(messages)

        return {
            "total_conversations": total,
            "total_messages": total_messages,
        }


class ConversationManagerWithPersistence:
    """带持久化的对话管理器"""

    def __init__(
        self,
        llm_integration,
        store: ConversationStore | None = None,
        system_prompt: str | None = None,
    ):
        """
        初始化对话管理器

        Args:
            llm_integration: LLM 集成实例
            store: 对话存储实例
            system_prompt: 系统提示
        """
        self.llm = llm_integration
        self.store = store or ConversationStore()
        self.system_prompt = system_prompt
        self.current_conversation: Conversation | None = None

    def create_conversation(
        self,
        title: str = "新对话",
        metadata: dict[str, Any] | None = None,
    ) -> Conversation:
        """创建新对话"""
        import uuid

        now = datetime.now().isoformat()

        conversation = Conversation(
            id=str(uuid.uuid4()),
            title=title,
            messages=[],
            created_at=now,
            updated_at=now,
            metadata=metadata,
        )

        if self.system_prompt:
            conversation.messages.append(
                Message(
                    role="system",
                    content=self.system_prompt,
                    timestamp=now,
                )
            )

        self.store.save_conversation(conversation)
        self.current_conversation = conversation
        return conversation

    def load_conversation(self, conversation_id: str) -> Conversation | None:
        """加载对话"""
        conversation = self.store.get_conversation(conversation_id)
        if conversation:
            self.current_conversation = conversation
        return conversation

    def add_message(
        self,
        role: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> Message:
        """添加消息"""
        if not self.current_conversation:
            self.create_conversation()

        now = datetime.now().isoformat()
        message = Message(
            role=role,
            content=content,
            timestamp=now,
            metadata=metadata,
        )

        self.current_conversation.messages.append(message)
        self.current_conversation.updated_at = now

        if role == "user" and len(self.current_conversation.messages) == 2:
            self.current_conversation.title = content[:50] + ("..." if len(content) > 50 else "")

        self.store.save_conversation(self.current_conversation)
        return message

    def converse(self, user_input: str) -> str:
        """进行对话"""
        self.add_message("user", user_input)

        messages = [
            {"role": m.role, "content": m.content} for m in self.current_conversation.messages
        ]
        response = self.llm.chat(messages)

        self.add_message("assistant", response)
        return response

    def get_history(self) -> list[dict[str, str]]:
        """获取对话历史"""
        if not self.current_conversation:
            return []
        return [{"role": m.role, "content": m.content} for m in self.current_conversation.messages]

    def clear_history(self):
        """清空当前对话历史"""
        if self.current_conversation:
            system_messages = [m for m in self.current_conversation.messages if m.role == "system"]
            self.current_conversation.messages = system_messages
            self.current_conversation.updated_at = datetime.now().isoformat()
            self.store.save_conversation(self.current_conversation)

    def list_conversations(self, limit: int = 20) -> list[Conversation]:
        """列出所有对话"""
        return self.store.list_conversations(limit=limit)

    def delete_conversation(self, conversation_id: str) -> bool:
        """删除对话"""
        result = self.store.delete_conversation(conversation_id)
        if self.current_conversation and self.current_conversation.id == conversation_id:
            self.current_conversation = None
        return result

    def search_conversations(self, query: str) -> list[Conversation]:
        """搜索对话"""
        return self.store.search_conversations(query)

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return self.store.get_stats()
