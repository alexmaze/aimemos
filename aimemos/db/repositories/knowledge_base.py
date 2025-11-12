"""知识库数据访问仓储。"""

import json
from datetime import datetime
from typing import Optional
from uuid import uuid4

from ...models.knowledge_base import KnowledgeBase
from ...schemas.knowledge_base import KnowledgeBaseCreate, KnowledgeBaseUpdate
from ..database import get_database


class KnowledgeBaseRepository:
    """知识库数据访问仓储。"""
    
    def __init__(self):
        """初始化知识库仓储。"""
        self.db = get_database()
        self._init_table()
    
    def _init_table(self):
        """初始化知识库表结构和索引。"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # 创建知识库表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_bases (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    cover_image TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)
            
            # 创建索引以提高查询性能
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_knowledge_bases_user_id 
                ON knowledge_bases (user_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_knowledge_bases_created_at 
                ON knowledge_bases (created_at DESC)
            """)
            
            conn.commit()
    
    def create(self, user_id: str, kb_data: KnowledgeBaseCreate) -> KnowledgeBase:
        """为指定用户创建新知识库。"""
        kb_id = str(uuid4())
        now = datetime.utcnow()
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO knowledge_bases (id, user_id, name, description, cover_image, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    kb_id,
                    user_id,
                    kb_data.name,
                    kb_data.description,
                    kb_data.cover_image,
                    now.isoformat(),
                    now.isoformat()
                )
            )
        
        return KnowledgeBase(
            id=kb_id,
            user_id=user_id,
            name=kb_data.name,
            description=kb_data.description,
            cover_image=kb_data.cover_image,
            created_at=now,
            updated_at=now,
        )
    
    def get_by_id(self, user_id: str, kb_id: str) -> Optional[KnowledgeBase]:
        """获取用户的指定知识库。"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT id, user_id, name, description, cover_image, created_at, updated_at
                   FROM knowledge_bases WHERE id = ? AND user_id = ?""",
                (kb_id, user_id)
            )
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return KnowledgeBase(
                id=row["id"],
                user_id=row["user_id"],
                name=row["name"],
                description=row["description"],
                cover_image=row["cover_image"],
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"])
            )
    
    def list_by_user(
        self, 
        user_id: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> tuple[list[KnowledgeBase], int]:
        """列出用户的知识库，支持分页。"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # 获取总数
            cursor.execute(
                "SELECT COUNT(*) as count FROM knowledge_bases WHERE user_id = ?",
                (user_id,)
            )
            total = cursor.fetchone()["count"]
            
            # 获取分页数据
            cursor.execute(
                """SELECT id, user_id, name, description, cover_image, created_at, updated_at
                   FROM knowledge_bases WHERE user_id = ?
                   ORDER BY created_at DESC
                   LIMIT ? OFFSET ?""",
                (user_id, limit, skip)
            )
            
            items = [
                KnowledgeBase(
                    id=row["id"],
                    user_id=row["user_id"],
                    name=row["name"],
                    description=row["description"],
                    cover_image=row["cover_image"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"])
                )
                for row in cursor.fetchall()
            ]
            
            return items, total
    
    def update(
        self, 
        user_id: str, 
        kb_id: str, 
        kb_data: KnowledgeBaseUpdate
    ) -> Optional[KnowledgeBase]:
        """更新用户的知识库。"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # 先获取现有知识库
            kb = self.get_by_id(user_id, kb_id)
            if not kb:
                return None
            
            # 准备更新数据
            update_dict = kb_data.model_dump(exclude_unset=True)
            updated_at = datetime.utcnow()
            
            # 更新字段
            name = update_dict.get("name", kb.name)
            description = update_dict.get("description", kb.description)
            cover_image = update_dict.get("cover_image", kb.cover_image)
            
            cursor.execute(
                """UPDATE knowledge_bases 
                   SET name = ?, description = ?, cover_image = ?, updated_at = ?
                   WHERE id = ? AND user_id = ?""",
                (name, description, cover_image, updated_at.isoformat(), kb_id, user_id)
            )
            
            return KnowledgeBase(
                id=kb_id,
                user_id=user_id,
                name=name,
                description=description,
                cover_image=cover_image,
                created_at=kb.created_at,
                updated_at=updated_at
            )
    
    def delete(self, user_id: str, kb_id: str) -> bool:
        """删除用户的知识库。"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM knowledge_bases WHERE id = ? AND user_id = ?",
                (kb_id, user_id)
            )
            return cursor.rowcount > 0
