"""聊天会话仓储。"""

import sqlite3
from typing import List, Optional
from datetime import datetime
import uuid

from ..database import get_database
from ...models.chat_session import ChatSession


class ChatSessionRepository:
    """聊天会话数据访问仓储。"""
    
    def __init__(self):
        """初始化仓储并创建表结构。"""
        self.db = get_database()
        self._ensure_table()
    
    def _ensure_table(self):
        """确保表结构存在并创建索引。"""
        with self.db.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    knowledge_base_id TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            # 创建索引
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id 
                ON chat_sessions(user_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_chat_sessions_created_at 
                ON chat_sessions(created_at DESC)
            """)
            conn.commit()
    
    def create(self, user_id: str, title: str, knowledge_base_id: Optional[str] = None) -> ChatSession:
        """创建新的聊天会话。"""
        session_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        with self.db.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO chat_sessions (id, user_id, title, knowledge_base_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (session_id, user_id, title, knowledge_base_id, now, now)
            )
            conn.commit()
        
        return self.get_by_id(session_id, user_id)
    
    def get_by_id(self, session_id: str, user_id: str) -> Optional[ChatSession]:
        """根据ID获取聊天会话。"""
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT id, user_id, title, knowledge_base_id, created_at, updated_at
                FROM chat_sessions
                WHERE id = ? AND user_id = ?
                """,
                (session_id, user_id)
            )
            row = cursor.fetchone()
            
            if row:
                return ChatSession(
                    id=row[0],
                    user_id=row[1],
                    title=row[2],
                    knowledge_base_id=row[3],
                    created_at=datetime.fromisoformat(row[4]),
                    updated_at=datetime.fromisoformat(row[5])
                )
            return None
    
    def list_by_user(self, user_id: str, skip: int = 0, limit: int = 100) -> List[ChatSession]:
        """获取用户的所有聊天会话。"""
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT id, user_id, title, knowledge_base_id, created_at, updated_at
                FROM chat_sessions
                WHERE user_id = ?
                ORDER BY updated_at DESC
                LIMIT ? OFFSET ?
                """,
                (user_id, limit, skip)
            )
            rows = cursor.fetchall()
            
            return [
                ChatSession(
                    id=row[0],
                    user_id=row[1],
                    title=row[2],
                    knowledge_base_id=row[3],
                    created_at=datetime.fromisoformat(row[4]),
                    updated_at=datetime.fromisoformat(row[5])
                )
                for row in rows
            ]
    
    def update(self, session_id: str, user_id: str, title: Optional[str] = None, 
               knowledge_base_id: Optional[str] = None) -> Optional[ChatSession]:
        """更新聊天会话。"""
        session = self.get_by_id(session_id, user_id)
        if not session:
            return None
        
        now = datetime.utcnow().isoformat()
        
        # 准备更新字段
        update_fields = ["updated_at = ?"]
        params = [now]
        
        if title is not None:
            update_fields.append("title = ?")
            params.append(title)
        
        if knowledge_base_id is not None:
            update_fields.append("knowledge_base_id = ?")
            params.append(knowledge_base_id)
        
        params.extend([session_id, user_id])
        
        with self.db.get_connection() as conn:
            conn.execute(
                f"""
                UPDATE chat_sessions
                SET {', '.join(update_fields)}
                WHERE id = ? AND user_id = ?
                """,
                params
            )
            conn.commit()
        
        return self.get_by_id(session_id, user_id)
    
    def delete(self, session_id: str, user_id: str) -> bool:
        """删除聊天会话。"""
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                """
                DELETE FROM chat_sessions
                WHERE id = ? AND user_id = ?
                """,
                (session_id, user_id)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def touch(self, session_id: str, user_id: str) -> None:
        """更新会话的 updated_at 时间戳。"""
        now = datetime.utcnow().isoformat()
        with self.db.get_connection() as conn:
            conn.execute(
                """
                UPDATE chat_sessions
                SET updated_at = ?
                WHERE id = ? AND user_id = ?
                """,
                (now, session_id, user_id)
            )
            conn.commit()
