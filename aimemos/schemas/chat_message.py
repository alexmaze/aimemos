"""聊天消息的 Pydantic 模式。"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ChatMessageCreate(BaseModel):
    """创建聊天消息的请求模式。"""
    
    content: str = Field(..., min_length=1, max_length=10000, description="消息内容")


class ChatMessageResponse(BaseModel):
    """聊天消息的响应模式。"""
    
    id: str = Field(..., description="消息ID")
    session_id: str = Field(..., description="会话ID")
    role: str = Field(..., description="角色：user 或 assistant")
    content: str = Field(..., description="消息内容")
    rag_context: Optional[str] = Field(None, description="RAG检索到的上下文")
    rag_sources: Optional[List[Dict[str, Any]]] = Field(None, description="RAG来源信息")
    created_at: datetime = Field(..., description="创建时间")
    
    class Config:
        from_attributes = True


class ChatStreamChunk(BaseModel):
    """流式聊天响应的数据块。"""
    
    type: str = Field(..., description="数据块类型：message, rag_step, done, error")
    content: Optional[str] = Field(None, description="内容")
    step: Optional[str] = Field(None, description="RAG步骤名称")
    data: Optional[Dict[str, Any]] = Field(None, description="步骤数据")
