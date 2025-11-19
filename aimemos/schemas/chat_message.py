"""聊天消息的 Pydantic 模式。"""

from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class ContentType(str, Enum):
    """内容类型枚举。"""
    THINKING = "thinking"  # 思考过程
    CONTENT = "content"    # 正文内容


class ChatMessageCreate(BaseModel):
    """创建聊天消息的请求模式。"""
    
    content: str = Field(..., min_length=1, max_length=10000, description="消息内容")


class ChatMessageResponse(BaseModel):
    """聊天消息的响应模式。"""
    
    id: str = Field(..., description="消息ID")
    session_id: str = Field(..., description="会话ID")
    role: str = Field(..., description="角色：user 或 assistant")
    content: str = Field(..., description="消息内容")
    content_type: ContentType = Field(ContentType.CONTENT, description="内容类型：thinking(思考过程) 或 content(正文)")
    rag_context: Optional[str] = Field(None, description="RAG检索到的上下文")
    rag_sources: Optional[List[Dict[str, Any]]] = Field(None, description="RAG来源信息")
    created_at: datetime = Field(..., description="创建时间")
    
    class Config:
        from_attributes = True


class ChatStreamChunk(BaseModel):
    """流式聊天响应的数据块。
    
    定义了固定格式的流式响应数据结构，用于替代直接的JSON格式。
    """
    
    type: Literal["message", "rag_step", "done", "error"] = Field(..., description="数据块类型：message(消息), rag_step(RAG步骤), done(完成), error(错误)")
    content: Optional[str] = Field(None, description="消息内容（type=message时使用）")
    content_type: Optional[ContentType] = Field(None, description="内容类型：thinking(思考过程) 或 content(正文)，仅在type=message时有效")
    step: Optional[str] = Field(None, description="RAG步骤名称（type=rag_step时使用）")
    data: Optional[Dict[str, Any]] = Field(None, description="步骤数据或错误详情")
