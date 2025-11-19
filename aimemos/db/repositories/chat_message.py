"""聊天消息仓储。"""

import sqlite3
from typing import List, Optional
from datetime import datetime
import uuid
import json

from ..database import get_database
from ...models.chat_message import ChatMessage


class ChatMessageRepository:
    """聊天消息数据访问仓储。"""
    
    def __init__(self):
        """初始化仓储并创建表结构。"""
        self.db = get_database()
        self._ensure_table()
    
    def _ensure_table(self):
        """确保表结构存在并创建索引。"""
        with self.db.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    thinking_process TEXT,
                    content TEXT NOT NULL,
                    rag_context TEXT,
                    rag_sources TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
                )
            """)
            
            # Add thinking_process column if it doesn't exist (migration for existing databases)
            try:
                conn.execute("""
                    ALTER TABLE chat_messages ADD COLUMN thinking_process TEXT
                """)
            except sqlite3.OperationalError:
                # Column already exists, ignore
                pass
            
            # 创建索引
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id 
                ON chat_messages(session_id, created_at)
            """)
            conn.commit()
    
    def create(
        self,
        session_id: str,
        role: str,
        content: str,
        thinking_process: Optional[str] = None,
        rag_context: Optional[str] = None,
        rag_sources: Optional[str] = None
    ) -> ChatMessage:
        """创建新的聊天消息。"""
        message_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        with self.db.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO chat_messages (id, session_id, role, thinking_process, content, rag_context, rag_sources, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (message_id, session_id, role, thinking_process, content, rag_context, rag_sources, now)
            )
            conn.commit()
        
        return self.get_by_id(message_id)
    
    def get_by_id(self, message_id: str) -> Optional[ChatMessage]:
        """根据ID获取聊天消息。"""
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT id, session_id, role, thinking_process, content, rag_context, rag_sources, created_at
                FROM chat_messages
                WHERE id = ?
                """,
                (message_id,)
            )
            row = cursor.fetchone()
            
            if row:
                return ChatMessage(
                    id=row[0],
                    session_id=row[1],
                    role=row[2],
                    thinking_process=row[3],
                    content=row[4],
                    rag_context=row[5],
                    rag_sources=row[6],
                    created_at=datetime.fromisoformat(row[7])
                )
            return None
    
    def list_by_session(
        self,
        session_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[ChatMessage]:
        """获取会话的所有消息。"""
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT id, session_id, role, thinking_process, content, rag_context, rag_sources, created_at
                FROM chat_messages
                WHERE session_id = ?
                ORDER BY created_at ASC
                LIMIT ? OFFSET ?
                """,
                (session_id, limit, skip)
            )
            rows = cursor.fetchall()
            
            return [
                ChatMessage(
                    id=row[0],
                    session_id=row[1],
                    role=row[2],
                    thinking_process=row[3],
                    content=row[4],
                    rag_context=row[5],
                    rag_sources=row[6],
                    created_at=datetime.fromisoformat(row[7])
                )
                for row in rows
            ]
    
    def delete_by_session(self, session_id: str) -> int:
        """删除会话的所有消息。"""
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                """
                DELETE FROM chat_messages
                WHERE session_id = ?
                """,
                (session_id,)
            )
            conn.commit()
            return cursor.rowcount
