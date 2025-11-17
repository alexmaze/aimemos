"""聊天会话的 Pydantic 模式。"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ChatSessionCreate(BaseModel):
    """创建聊天会话的请求模式。"""
    
    title: str = Field(..., min_length=1, max_length=200, description="会话标题")
    knowledge_base_id: Optional[str] = Field(None, description="关联的知识库ID（可选）")


class ChatSessionUpdate(BaseModel):
    """更新聊天会话的请求模式。"""
    
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="会话标题")
    knowledge_base_id: Optional[str] = Field(None, description="关联的知识库ID")


class ChatSessionResponse(BaseModel):
    """聊天会话的响应模式。"""
    
    id: str = Field(..., description="会话ID")
    user_id: str = Field(..., description="用户ID")
    title: str = Field(..., description="会话标题")
    knowledge_base_id: Optional[str] = Field(None, description="关联的知识库ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True
