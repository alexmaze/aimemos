"""文档数据访问仓储。"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from ...models.document import Document
from ...schemas.document import DocumentCreate, DocumentUpdate
from ..database import get_database


class DocumentRepository:
    """文档数据访问仓储。"""
    
    def __init__(self):
        """初始化文档仓储。"""
        self.db = get_database()
        self._init_table()
    
    def _init_table(self):
        """初始化文档表结构和索引。"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # 创建文档表（包含文件夹）
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    knowledge_base_id TEXT NOT NULL,
                    folder_id TEXT,
                    user_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    doc_type TEXT NOT NULL,
                    summary TEXT,
                    content TEXT NOT NULL DEFAULT '',
                    path TEXT,
                    source_file_path TEXT,
                    source_file_size INTEGER,
                    source_file_format TEXT,
                    source_file_created_at TEXT,
                    source_file_modified_at TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (knowledge_base_id) REFERENCES knowledge_bases (id) ON DELETE CASCADE,
                    FOREIGN KEY (folder_id) REFERENCES documents (id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)
            
            # 创建索引
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_documents_kb_id 
                ON documents (knowledge_base_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_documents_folder_id 
                ON documents (folder_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_documents_user_id 
                ON documents (user_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_documents_type 
                ON documents (doc_type)
            """)
            
            conn.commit()
    
    def create_note(
        self, 
        user_id: str, 
        kb_id: str, 
        doc_data: DocumentCreate
    ) -> Document:
        """创建新笔记文档。"""
        doc_id = str(uuid4())
        now = datetime.utcnow()
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO documents (
                    id, knowledge_base_id, folder_id, user_id, name, doc_type, 
                    summary, content, created_at, updated_at
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    doc_id,
                    kb_id,
                    doc_data.folder_id,
                    user_id,
                    doc_data.name,
                    'note',
                    doc_data.summary,
                    doc_data.content,
                    now.isoformat(),
                    now.isoformat()
                )
            )
        
        return Document(
            id=doc_id,
            knowledge_base_id=kb_id,
            folder_id=doc_data.folder_id,
            user_id=user_id,
            name=doc_data.name,
            doc_type='note',
            summary=doc_data.summary,
            content=doc_data.content,
            created_at=now,
            updated_at=now,
        )
    
    def create_folder(
        self,
        user_id: str,
        kb_id: str,
        name: str,
        parent_folder_id: Optional[str] = None
    ) -> Document:
        """创建文件夹（作为特殊类型的文档）。"""
        folder_id = str(uuid4())
        now = datetime.utcnow()
        
        # 构建路径
        if not parent_folder_id:
            path = f"/{name}"
        else:
            # 获取父文件夹路径
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT path FROM documents WHERE id = ? AND knowledge_base_id = ? AND doc_type = 'folder'",
                    (parent_folder_id, kb_id)
                )
                row = cursor.fetchone()
                if not row:
                    raise ValueError("父文件夹不存在")
                parent_path = row["path"]
                path = f"{parent_path}/{name}"
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO documents (
                    id, knowledge_base_id, folder_id, user_id, name, doc_type, 
                    summary, content, path, created_at, updated_at
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    folder_id,
                    kb_id,
                    parent_folder_id,
                    user_id,
                    name,
                    'folder',
                    None,
                    '',
                    path,
                    now.isoformat(),
                    now.isoformat()
                )
            )
        
        return Document(
            id=folder_id,
            knowledge_base_id=kb_id,
            folder_id=parent_folder_id,
            user_id=user_id,
            name=name,
            doc_type='folder',
            summary=None,
            content='',
            path=path,
            created_at=now,
            updated_at=now,
        )
    
    def create_uploaded(
        self,
        doc_id: str,
        user_id: str,
        kb_id: str,
        name: str,
        folder_id: Optional[str],
        content: str,
        source_file_path: str,
        source_file_size: int,
        source_file_format: str,
        source_file_created_at: Optional[datetime] = None,
        source_file_modified_at: Optional[datetime] = None,
        summary: Optional[str] = None
    ) -> Document:
        """创建上传文档记录。
        
        Args:
            doc_id: 文档ID（预先生成，用于文件命名）
            其他参数同上
        """
        now = datetime.utcnow()
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO documents (
                    id, knowledge_base_id, folder_id, user_id, name, doc_type, 
                    summary, content, source_file_path, source_file_size, source_file_format,
                    source_file_created_at, source_file_modified_at, created_at, updated_at
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    doc_id,
                    kb_id,
                    folder_id,
                    user_id,
                    name,
                    'uploaded',
                    summary,
                    content,
                    source_file_path,
                    source_file_size,
                    source_file_format,
                    source_file_created_at.isoformat() if source_file_created_at else None,
                    source_file_modified_at.isoformat() if source_file_modified_at else None,
                    now.isoformat(),
                    now.isoformat()
                )
            )
        
        return Document(
            id=doc_id,
            knowledge_base_id=kb_id,
            folder_id=folder_id,
            user_id=user_id,
            name=name,
            doc_type='uploaded',
            summary=summary,
            content=content,
            source_file_path=source_file_path,
            source_file_size=source_file_size,
            source_file_format=source_file_format,
            source_file_created_at=source_file_created_at,
            source_file_modified_at=source_file_modified_at,
            created_at=now,
            updated_at=now,
        )
    
    def get_by_id(self, user_id: str, doc_id: str) -> Optional[Document]:
        """获取指定文档或文件夹。"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT id, knowledge_base_id, folder_id, user_id, name, doc_type, summary, 
                          content, path, source_file_path, source_file_size, source_file_format,
                          source_file_created_at, source_file_modified_at, created_at, updated_at
                   FROM documents WHERE id = ? AND user_id = ?""",
                (doc_id, user_id)
            )
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return Document(
                id=row["id"],
                knowledge_base_id=row["knowledge_base_id"],
                folder_id=row["folder_id"],
                user_id=row["user_id"],
                name=row["name"],
                doc_type=row["doc_type"],
                summary=row["summary"],
                content=row["content"] or "",
                path=row["path"],
                source_file_path=row["source_file_path"],
                source_file_size=row["source_file_size"],
                source_file_format=row["source_file_format"],
                source_file_created_at=datetime.fromisoformat(row["source_file_created_at"]) if row["source_file_created_at"] else None,
                source_file_modified_at=datetime.fromisoformat(row["source_file_modified_at"]) if row["source_file_modified_at"] else None,
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"])
            )
    
    def list_by_kb(
        self, 
        user_id: str, 
        kb_id: str,
        folder_id: Optional[str] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> tuple[list[Document], int]:
        """列出知识库中的文档和文件夹，支持按文件夹过滤和分页。
        
        文件夹会排在前面，然后是文件，这样更符合文件浏览器的体验。
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            if folder_id is None:
                # 获取根目录下的文档和文件夹
                cursor.execute(
                    "SELECT COUNT(*) as count FROM documents WHERE knowledge_base_id = ? AND user_id = ? AND folder_id IS NULL",
                    (kb_id, user_id)
                )
                total = cursor.fetchone()["count"]
                
                cursor.execute(
                    """SELECT id, knowledge_base_id, folder_id, user_id, name, doc_type, summary, 
                              content, path, source_file_path, source_file_size, source_file_format,
                              source_file_created_at, source_file_modified_at, created_at, updated_at
                       FROM documents WHERE knowledge_base_id = ? AND user_id = ? AND folder_id IS NULL
                       ORDER BY 
                           CASE doc_type 
                               WHEN 'folder' THEN 0 
                               ELSE 1 
                           END,
                           name ASC
                       LIMIT ? OFFSET ?""",
                    (kb_id, user_id, limit, skip)
                )
            else:
                # 获取指定文件夹下的文档和子文件夹
                cursor.execute(
                    "SELECT COUNT(*) as count FROM documents WHERE knowledge_base_id = ? AND user_id = ? AND folder_id = ?",
                    (kb_id, user_id, folder_id)
                )
                total = cursor.fetchone()["count"]
                
                cursor.execute(
                    """SELECT id, knowledge_base_id, folder_id, user_id, name, doc_type, summary, 
                              content, path, source_file_path, source_file_size, source_file_format,
                              source_file_created_at, source_file_modified_at, created_at, updated_at
                       FROM documents WHERE knowledge_base_id = ? AND user_id = ? AND folder_id = ?
                       ORDER BY 
                           CASE doc_type 
                               WHEN 'folder' THEN 0 
                               ELSE 1 
                           END,
                           name ASC
                       LIMIT ? OFFSET ?""",
                    (kb_id, user_id, folder_id, limit, skip)
                )
            
            items = [
                Document(
                    id=row["id"],
                    knowledge_base_id=row["knowledge_base_id"],
                    folder_id=row["folder_id"],
                    user_id=row["user_id"],
                    name=row["name"],
                    doc_type=row["doc_type"],
                    summary=row["summary"],
                    content=row["content"] or "",
                    path=row["path"],
                    source_file_path=row["source_file_path"],
                    source_file_size=row["source_file_size"],
                    source_file_format=row["source_file_format"],
                    source_file_created_at=datetime.fromisoformat(row["source_file_created_at"]) if row["source_file_created_at"] else None,
                    source_file_modified_at=datetime.fromisoformat(row["source_file_modified_at"]) if row["source_file_modified_at"] else None,
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"])
                )
                for row in cursor.fetchall()
            ]
            
            return items, total
    
    def update(
        self, 
        user_id: str, 
        doc_id: str, 
        doc_data: DocumentUpdate
    ) -> Optional[Document]:
        """更新文档（笔记可以更新内容，上传文档和文件夹只能更新元数据）。"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # 先获取现有文档
            doc = self.get_by_id(user_id, doc_id)
            if not doc:
                return None
            
            # 准备更新数据
            update_dict = doc_data.model_dump(exclude_unset=True)
            updated_at = datetime.utcnow()
            
            # 更新字段
            name = update_dict.get("name", doc.name)
            summary = update_dict.get("summary", doc.summary)
            folder_id = update_dict.get("folder_id", doc.folder_id)
            
            # 如果是笔记，允许更新内容；如果是上传文档或文件夹，不允许更新内容
            if doc.doc_type == 'note':
                content = update_dict.get("content", doc.content)
            else:
                content = doc.content
            
            # 如果是文件夹且名称或父文件夹改变，需要更新路径
            path = doc.path
            if doc.doc_type == 'folder' and (name != doc.name or folder_id != doc.folder_id):
                if not folder_id:
                    path = f"/{name}"
                else:
                    # 获取父文件夹路径
                    cursor.execute(
                        "SELECT path FROM documents WHERE id = ? AND doc_type = 'folder'",
                        (folder_id,)
                    )
                    parent_row = cursor.fetchone()
                    if parent_row:
                        parent_path = parent_row["path"]
                        path = f"{parent_path}/{name}"
            
            cursor.execute(
                """UPDATE documents 
                   SET name = ?, summary = ?, content = ?, folder_id = ?, path = ?, updated_at = ?
                   WHERE id = ? AND user_id = ?""",
                (name, summary, content, folder_id, path, updated_at.isoformat(), doc_id, user_id)
            )
            
            return Document(
                id=doc_id,
                knowledge_base_id=doc.knowledge_base_id,
                folder_id=folder_id,
                user_id=user_id,
                name=name,
                doc_type=doc.doc_type,
                summary=summary,
                content=content,
                path=path,
                source_file_path=doc.source_file_path,
                source_file_size=doc.source_file_size,
                source_file_format=doc.source_file_format,
                source_file_created_at=doc.source_file_created_at,
                source_file_modified_at=doc.source_file_modified_at,
                created_at=doc.created_at,
                updated_at=updated_at
            )
    
    def delete(self, user_id: str, doc_id: str) -> bool:
        """删除文档。"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM documents WHERE id = ? AND user_id = ?",
                (doc_id, user_id)
            )
            return cursor.rowcount > 0
    
    def search(self, user_id: str, kb_id: str, query: str) -> list[Document]:
        """搜索知识库中的文档（不包括文件夹）。"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            query_pattern = f"%{query.lower()}%"
            
            cursor.execute(
                """SELECT id, knowledge_base_id, folder_id, user_id, name, doc_type, summary, 
                          content, path, source_file_path, source_file_size, source_file_format,
                          source_file_created_at, source_file_modified_at, created_at, updated_at
                   FROM documents 
                   WHERE knowledge_base_id = ? AND user_id = ? 
                   AND doc_type != 'folder'
                   AND (
                       LOWER(name) LIKE ? 
                       OR LOWER(content) LIKE ? 
                       OR LOWER(summary) LIKE ?
                   )
                   ORDER BY created_at DESC""",
                (kb_id, user_id, query_pattern, query_pattern, query_pattern)
            )
            
            results = [
                Document(
                    id=row["id"],
                    knowledge_base_id=row["knowledge_base_id"],
                    folder_id=row["folder_id"],
                    user_id=row["user_id"],
                    name=row["name"],
                    doc_type=row["doc_type"],
                    summary=row["summary"],
                    content=row["content"] or "",
                    path=row["path"],
                    source_file_path=row["source_file_path"],
                    source_file_size=row["source_file_size"],
                    source_file_format=row["source_file_format"],
                    source_file_created_at=datetime.fromisoformat(row["source_file_created_at"]) if row["source_file_created_at"] else None,
                    source_file_modified_at=datetime.fromisoformat(row["source_file_modified_at"]) if row["source_file_modified_at"] else None,
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"])
                )
                for row in cursor.fetchall()
            ]
            
            return results
