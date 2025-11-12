"""备忘录数据访问仓储。"""

import json
from datetime import datetime
from typing import Optional
from uuid import uuid4

from ...models.memo import Memo
from ...schemas.memo import MemoCreate, MemoUpdate
from ..database import get_database


class MemoRepository:
    """备忘录数据访问仓储。"""
    
    def __init__(self):
        """初始化备忘录仓储。"""
        self.db = get_database()
        self._init_table()
    
    def _init_table(self):
        """初始化备忘录表结构和索引。"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # 创建备忘录表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memos (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    tags TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)
            
            # 创建索引以提高查询性能
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_memos_user_id 
                ON memos (user_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_memos_created_at 
                ON memos (created_at DESC)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_memos_user_created 
                ON memos (user_id, created_at DESC)
            """)
            
            conn.commit()
    
    def create(self, user_id: str, memo_data: MemoCreate) -> Memo:
        """为指定用户创建新备忘录。"""
        memo_id = str(uuid4())
        now = datetime.utcnow()
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO memos (id, user_id, title, content, tags, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    memo_id,
                    user_id,
                    memo_data.title,
                    memo_data.content,
                    json.dumps(memo_data.tags),
                    now.isoformat(),
                    now.isoformat()
                )
            )
        
        return Memo(
            id=memo_id,
            user_id=user_id,
            title=memo_data.title,
            content=memo_data.content,
            tags=memo_data.tags,
            created_at=now,
            updated_at=now,
        )
    
    def get_by_id(self, user_id: str, memo_id: str) -> Optional[Memo]:
        """获取用户的指定备忘录。"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT id, user_id, title, content, tags, created_at, updated_at
                   FROM memos WHERE id = ? AND user_id = ?""",
                (memo_id, user_id)
            )
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return Memo(
                id=row["id"],
                user_id=row["user_id"],
                title=row["title"],
                content=row["content"],
                tags=json.loads(row["tags"]),
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"])
            )
    
    def list_by_user(
        self, 
        user_id: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> tuple[list[Memo], int]:
        """列出用户的备忘录，支持分页。"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # 获取总数
            cursor.execute(
                "SELECT COUNT(*) as count FROM memos WHERE user_id = ?",
                (user_id,)
            )
            total = cursor.fetchone()["count"]
            
            # 获取分页数据
            cursor.execute(
                """SELECT id, user_id, title, content, tags, created_at, updated_at
                   FROM memos WHERE user_id = ?
                   ORDER BY created_at DESC
                   LIMIT ? OFFSET ?""",
                (user_id, limit, skip)
            )
            
            items = [
                Memo(
                    id=row["id"],
                    user_id=row["user_id"],
                    title=row["title"],
                    content=row["content"],
                    tags=json.loads(row["tags"]),
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"])
                )
                for row in cursor.fetchall()
            ]
            
            return items, total
    
    def update(
        self, 
        user_id: str, 
        memo_id: str, 
        memo_data: MemoUpdate
    ) -> Optional[Memo]:
        """更新用户的备忘录。"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # 先获取现有备忘录
            memo = self.get_by_id(user_id, memo_id)
            if not memo:
                return None
            
            # 准备更新数据
            update_dict = memo_data.model_dump(exclude_unset=True)
            updated_at = datetime.utcnow()
            
            # 更新字段
            title = update_dict.get("title", memo.title)
            content = update_dict.get("content", memo.content)
            tags = update_dict.get("tags", memo.tags)
            
            cursor.execute(
                """UPDATE memos 
                   SET title = ?, content = ?, tags = ?, updated_at = ?
                   WHERE id = ? AND user_id = ?""",
                (title, content, json.dumps(tags), updated_at.isoformat(), memo_id, user_id)
            )
            
            return Memo(
                id=memo_id,
                user_id=user_id,
                title=title,
                content=content,
                tags=tags,
                created_at=memo.created_at,
                updated_at=updated_at
            )
    
    def delete(self, user_id: str, memo_id: str) -> bool:
        """删除用户的备忘录。"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM memos WHERE id = ? AND user_id = ?",
                (memo_id, user_id)
            )
            return cursor.rowcount > 0
    
    def search(self, user_id: str, query: str) -> list[Memo]:
        """搜索用户的备忘录。"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            query_pattern = f"%{query.lower()}%"
            
            cursor.execute(
                """SELECT id, user_id, title, content, tags, created_at, updated_at
                   FROM memos 
                   WHERE user_id = ? 
                   AND (
                       LOWER(title) LIKE ? 
                       OR LOWER(content) LIKE ? 
                       OR LOWER(tags) LIKE ?
                   )
                   ORDER BY created_at DESC""",
                (user_id, query_pattern, query_pattern, query_pattern)
            )
            
            results = [
                Memo(
                    id=row["id"],
                    user_id=row["user_id"],
                    title=row["title"],
                    content=row["content"],
                    tags=json.loads(row["tags"]),
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"])
                )
                for row in cursor.fetchall()
            ]
            
            return results
