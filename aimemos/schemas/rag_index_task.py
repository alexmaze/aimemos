"""RAG 索引任务相关的 Pydantic 模式。"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class RAGIndexTaskResponse(BaseModel):
    """RAG 索引任务响应模型。"""
    
    id: str = Field(..., description="任务ID")
    document_id: str = Field(..., description="关联的文档ID")
    user_id: str = Field(..., description="所属用户ID")
    knowledge_base_id: str = Field(..., description="所属知识库ID")
    
    status: str = Field(..., description="索引状态: pending, indexing, completed, failed, timeout")
    task_uuid: str = Field(..., description="任务的唯一标识符（UUID）")
    thread_id: Optional[int] = Field(None, description="执行线程 ID（用于调试）")
    
    started_at: Optional[datetime] = Field(None, description="索引开始时间")
    completed_at: Optional[datetime] = Field(None, description="索引完成时间")
    error: Optional[str] = Field(None, description="错误信息（如果失败）")
    
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True
