"""RAG 索引任务领域模型。"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class RAGIndexTask(BaseModel):
    """RAG 索引任务领域模型。
    
    用于跟踪文档的 RAG 索引任务状态。
    """
    
    id: str  # 任务ID (UUID)
    document_id: str  # 关联的文档ID
    user_id: str  # 所属用户ID
    knowledge_base_id: str  # 所属知识库ID
    
    status: str  # 'pending', 'indexing', 'completed', 'failed', 'timeout'
    task_uuid: str  # 任务的唯一标识符（UUID），用于防重复执行
    thread_id: Optional[int] = None  # 执行线程 ID（用于调试）
    
    started_at: Optional[datetime] = None  # 索引开始时间
    completed_at: Optional[datetime] = None  # 索引完成时间
    error: Optional[str] = None  # 错误信息（如果失败）
    
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
