"""文件夹数据访问仓储。"""

import os
from datetime import datetime
from typing import Optional
from uuid import uuid4

from ...models.folder import Folder
from ...schemas.folder import FolderCreate, FolderUpdate
from ..database import get_database


class FolderRepository:
    """文件夹数据访问仓储。"""
    
    def __init__(self):
        """初始化文件夹仓储。"""
        self.db = get_database()
        self._init_table()
    
    def _init_table(self):
        """初始化文件夹表结构和索引。"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # 创建文件夹表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS folders (
                    id TEXT PRIMARY KEY,
                    knowledge_base_id TEXT NOT NULL,
                    parent_folder_id TEXT,
                    user_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    path TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (knowledge_base_id) REFERENCES knowledge_bases (id) ON DELETE CASCADE,
                    FOREIGN KEY (parent_folder_id) REFERENCES folders (id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)
            
            # 创建索引
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_folders_kb_id 
                ON folders (knowledge_base_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_folders_parent_id 
                ON folders (parent_folder_id)
            """)
            
            conn.commit()
    
    def _build_path(self, kb_id: str, parent_folder_id: Optional[str], name: str) -> str:
        """构建文件夹路径。"""
        if not parent_folder_id:
            return f"/{name}"
        
        # 获取父文件夹路径
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT path FROM folders WHERE id = ? AND knowledge_base_id = ?",
                (parent_folder_id, kb_id)
            )
            row = cursor.fetchone()
            if not row:
                raise ValueError("父文件夹不存在")
            
            parent_path = row["path"]
            return f"{parent_path}/{name}"
    
    def create(
        self, 
        user_id: str, 
        kb_id: str, 
        folder_data: FolderCreate
    ) -> Folder:
        """创建新文件夹。"""
        folder_id = str(uuid4())
        now = datetime.utcnow()
        
        # 构建路径
        path = self._build_path(kb_id, folder_data.parent_folder_id, folder_data.name)
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO folders (id, knowledge_base_id, parent_folder_id, user_id, name, path, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    folder_id,
                    kb_id,
                    folder_data.parent_folder_id,
                    user_id,
                    folder_data.name,
                    path,
                    now.isoformat(),
                    now.isoformat()
                )
            )
        
        return Folder(
            id=folder_id,
            knowledge_base_id=kb_id,
            parent_folder_id=folder_data.parent_folder_id,
            user_id=user_id,
            name=folder_data.name,
            path=path,
            created_at=now,
            updated_at=now,
        )
    
    def get_by_id(self, user_id: str, folder_id: str) -> Optional[Folder]:
        """获取指定文件夹。"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT id, knowledge_base_id, parent_folder_id, user_id, name, path, created_at, updated_at
                   FROM folders WHERE id = ? AND user_id = ?""",
                (folder_id, user_id)
            )
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return Folder(
                id=row["id"],
                knowledge_base_id=row["knowledge_base_id"],
                parent_folder_id=row["parent_folder_id"],
                user_id=row["user_id"],
                name=row["name"],
                path=row["path"],
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"])
            )
    
    def list_by_kb(
        self, 
        user_id: str, 
        kb_id: str,
        parent_folder_id: Optional[str] = None
    ) -> tuple[list[Folder], int]:
        """列出知识库中的文件夹，可选择性过滤父文件夹。"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            if parent_folder_id is None:
                # 获取根目录下的文件夹
                cursor.execute(
                    "SELECT COUNT(*) as count FROM folders WHERE knowledge_base_id = ? AND user_id = ? AND parent_folder_id IS NULL",
                    (kb_id, user_id)
                )
                total = cursor.fetchone()["count"]
                
                cursor.execute(
                    """SELECT id, knowledge_base_id, parent_folder_id, user_id, name, path, created_at, updated_at
                       FROM folders WHERE knowledge_base_id = ? AND user_id = ? AND parent_folder_id IS NULL
                       ORDER BY name ASC""",
                    (kb_id, user_id)
                )
            else:
                # 获取指定父文件夹下的子文件夹
                cursor.execute(
                    "SELECT COUNT(*) as count FROM folders WHERE knowledge_base_id = ? AND user_id = ? AND parent_folder_id = ?",
                    (kb_id, user_id, parent_folder_id)
                )
                total = cursor.fetchone()["count"]
                
                cursor.execute(
                    """SELECT id, knowledge_base_id, parent_folder_id, user_id, name, path, created_at, updated_at
                       FROM folders WHERE knowledge_base_id = ? AND user_id = ? AND parent_folder_id = ?
                       ORDER BY name ASC""",
                    (kb_id, user_id, parent_folder_id)
                )
            
            items = [
                Folder(
                    id=row["id"],
                    knowledge_base_id=row["knowledge_base_id"],
                    parent_folder_id=row["parent_folder_id"],
                    user_id=row["user_id"],
                    name=row["name"],
                    path=row["path"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"])
                )
                for row in cursor.fetchall()
            ]
            
            return items, total
    
    def update(
        self, 
        user_id: str, 
        folder_id: str, 
        folder_data: FolderUpdate
    ) -> Optional[Folder]:
        """更新文件夹。"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # 先获取现有文件夹
            folder = self.get_by_id(user_id, folder_id)
            if not folder:
                return None
            
            # 准备更新数据
            update_dict = folder_data.model_dump(exclude_unset=True)
            updated_at = datetime.utcnow()
            
            # 更新字段
            name = update_dict.get("name", folder.name)
            parent_folder_id = update_dict.get("parent_folder_id", folder.parent_folder_id)
            
            # 重新构建路径
            path = self._build_path(folder.knowledge_base_id, parent_folder_id, name)
            
            cursor.execute(
                """UPDATE folders 
                   SET name = ?, parent_folder_id = ?, path = ?, updated_at = ?
                   WHERE id = ? AND user_id = ?""",
                (name, parent_folder_id, path, updated_at.isoformat(), folder_id, user_id)
            )
            
            # 如果有子文件夹或文档，需要更新它们的路径
            # 这里先简化处理，后续可以添加级联更新逻辑
            
            return Folder(
                id=folder_id,
                knowledge_base_id=folder.knowledge_base_id,
                parent_folder_id=parent_folder_id,
                user_id=user_id,
                name=name,
                path=path,
                created_at=folder.created_at,
                updated_at=updated_at
            )
    
    def delete(self, user_id: str, folder_id: str) -> bool:
        """删除文件夹（级联删除子文件夹和文档）。"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM folders WHERE id = ? AND user_id = ?",
                (folder_id, user_id)
            )
            return cursor.rowcount > 0
