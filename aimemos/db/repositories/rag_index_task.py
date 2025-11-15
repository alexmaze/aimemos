"""RAG 索引任务数据访问仓储。"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from ...models.rag_index_task import RAGIndexTask
from ..database import get_database


class RAGIndexTaskRepository:
    """RAG 索引任务数据访问仓储。"""
    
    def __init__(self):
        """初始化 RAG 索引任务仓储。"""
        self.db = get_database()
        self._init_table()
    
    def _init_table(self):
        """初始化 RAG 索引任务表结构和索引。"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # 创建 RAG 索引任务表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rag_index_tasks (
                    id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    knowledge_base_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    task_uuid TEXT NOT NULL,
                    thread_id INTEGER,
                    started_at TEXT,
                    completed_at TEXT,
                    error TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users (user_id),
                    FOREIGN KEY (knowledge_base_id) REFERENCES knowledge_bases (id) ON DELETE CASCADE
                )
            """)
            
            # 创建索引
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_rag_index_tasks_document_id 
                ON rag_index_tasks (document_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_rag_index_tasks_user_id 
                ON rag_index_tasks (user_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_rag_index_tasks_kb_id 
                ON rag_index_tasks (knowledge_base_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_rag_index_tasks_status 
                ON rag_index_tasks (status)
            """)
            
            cursor.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_rag_index_tasks_doc_user 
                ON rag_index_tasks (document_id, user_id)
            """)
            
            conn.commit()
    
    def create(
        self,
        document_id: str,
        user_id: str,
        knowledge_base_id: str,
        task_uuid: str,
        status: str = 'pending'
    ) -> RAGIndexTask:
        """创建新的 RAG 索引任务。
        
        Args:
            document_id: 文档ID
            user_id: 用户ID
            knowledge_base_id: 知识库ID
            task_uuid: 任务UUID
            status: 初始状态
            
        Returns:
            创建的 RAG 索引任务对象
        """
        task_id = str(uuid4())
        now = datetime.now().isoformat()
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO rag_index_tasks 
                (id, document_id, user_id, knowledge_base_id, status, task_uuid, 
                 created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (task_id, document_id, user_id, knowledge_base_id, status, 
                  task_uuid, now, now))
            conn.commit()
        
        return self.get_by_id(task_id)
    
    def get_by_id(self, task_id: str) -> Optional[RAGIndexTask]:
        """根据任务ID获取 RAG 索引任务。
        
        Args:
            task_id: 任务ID
            
        Returns:
            RAG 索引任务对象，如果不存在则返回 None
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM rag_index_tasks WHERE id = ?
            """, (task_id,))
            row = cursor.fetchone()
        
        if not row:
            return None
        
        return self._row_to_task(row)
    
    def get_by_document_id(self, document_id: str, user_id: str) -> Optional[RAGIndexTask]:
        """根据文档ID获取 RAG 索引任务。
        
        Args:
            document_id: 文档ID
            user_id: 用户ID
            
        Returns:
            RAG 索引任务对象，如果不存在则返回 None
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM rag_index_tasks 
                WHERE document_id = ? AND user_id = ?
            """, (document_id, user_id))
            row = cursor.fetchone()
        
        if not row:
            return None
        
        return self._row_to_task(row)
    
    def update(
        self,
        task_id: str,
        status: Optional[str] = None,
        thread_id: Optional[int] = None,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        error: Optional[str] = None
    ) -> Optional[RAGIndexTask]:
        """更新 RAG 索引任务。
        
        Args:
            task_id: 任务ID
            status: 更新后的状态
            thread_id: 线程ID
            started_at: 开始时间
            completed_at: 完成时间
            error: 错误信息
            
        Returns:
            更新后的 RAG 索引任务对象
        """
        updates = []
        params = []
        
        if status is not None:
            updates.append("status = ?")
            params.append(status)
        
        if thread_id is not None:
            updates.append("thread_id = ?")
            params.append(thread_id)
        
        if started_at is not None:
            updates.append("started_at = ?")
            params.append(started_at.isoformat() if started_at else None)
        
        if completed_at is not None:
            updates.append("completed_at = ?")
            params.append(completed_at.isoformat() if completed_at else None)
        
        if error is not None:
            updates.append("error = ?")
            params.append(error)
        
        if not updates:
            return self.get_by_id(task_id)
        
        updates.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        params.append(task_id)
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE rag_index_tasks 
                SET {', '.join(updates)}
                WHERE id = ?
            """, params)
            conn.commit()
        
        return self.get_by_id(task_id)
    
    def upsert(
        self,
        document_id: str,
        user_id: str,
        knowledge_base_id: str,
        task_uuid: str,
        status: str = 'pending'
    ) -> RAGIndexTask:
        """创建或更新 RAG 索引任务。
        
        如果该文档已有任务，则更新；否则创建新任务。
        
        Args:
            document_id: 文档ID
            user_id: 用户ID
            knowledge_base_id: 知识库ID
            task_uuid: 任务UUID
            status: 状态
            
        Returns:
            RAG 索引任务对象
        """
        existing = self.get_by_document_id(document_id, user_id)
        
        if existing:
            # 更新现有任务
            task_id = existing.id
            now = datetime.now().isoformat()
            
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE rag_index_tasks 
                    SET task_uuid = ?, status = ?, thread_id = NULL, 
                        started_at = NULL, completed_at = NULL, error = NULL,
                        updated_at = ?
                    WHERE id = ?
                """, (task_uuid, status, now, task_id))
                conn.commit()
            
            return self.get_by_id(task_id)
        else:
            # 创建新任务
            return self.create(document_id, user_id, knowledge_base_id, task_uuid, status)
    
    def delete_by_document_id(self, document_id: str, user_id: str) -> bool:
        """删除文档的 RAG 索引任务。
        
        Args:
            document_id: 文档ID
            user_id: 用户ID
            
        Returns:
            是否删除成功
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM rag_index_tasks 
                WHERE document_id = ? AND user_id = ?
            """, (document_id, user_id))
            conn.commit()
            return cursor.rowcount > 0
    
    def check_timeout(
        self,
        task_id: str,
        timeout_seconds: int
    ) -> Optional[RAGIndexTask]:
        """检查任务是否超时，如果超时则更新状态。
        
        Args:
            task_id: 任务ID
            timeout_seconds: 超时时间（秒）
            
        Returns:
            更新后的任务对象（如果超时），否则返回 None
        """
        task = self.get_by_id(task_id)
        if not task or task.status != 'indexing' or not task.started_at:
            return None
        
        elapsed = (datetime.now() - task.started_at).total_seconds()
        if elapsed > timeout_seconds:
            return self.update(
                task_id,
                status='timeout',
                error=f'Task exceeded timeout limit of {timeout_seconds} seconds'
            )
        
        return None
    
    def _row_to_task(self, row) -> RAGIndexTask:
        """将数据库行转换为 RAG 索引任务对象。"""
        return RAGIndexTask(
            id=row[0],
            document_id=row[1],
            user_id=row[2],
            knowledge_base_id=row[3],
            status=row[4],
            task_uuid=row[5],
            thread_id=row[6],
            started_at=datetime.fromisoformat(row[7]) if row[7] else None,
            completed_at=datetime.fromisoformat(row[8]) if row[8] else None,
            error=row[9],
            created_at=datetime.fromisoformat(row[10]),
            updated_at=datetime.fromisoformat(row[11])
        )
