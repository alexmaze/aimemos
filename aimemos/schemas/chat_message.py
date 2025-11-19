"""聊天消息的 Pydantic 模式。"""

from typing import Optional, List, Dict, Any, Literal
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
    thinking_process: Optional[str] = Field(None, description="思考过程（如果有）")
    content: str = Field(..., description="消息正文内容")
    rag_context: Optional[str] = Field(None, description="RAG检索到的上下文")
    rag_sources: Optional[List[Dict[str, Any]]] = Field(None, description="RAG来源信息")
    created_at: datetime = Field(..., description="创建时间")
    
    class Config:
        from_attributes = True


class ChatStreamChunk(BaseModel):
    """流式聊天响应的数据块。
    
    定义了固定格式的流式响应数据结构，用于替代直接的JSON格式。
    """
    
    type: Literal["thinking", "content", "rag_step", "done", "error"] = Field(..., description="数据块类型：thinking(思考过程), content(正文内容), rag_step(RAG步骤), done(完成), error(错误)")
    text: Optional[str] = Field(None, description="文本内容（type=thinking或content时使用）")
    step: Optional[str] = Field(None, description="RAG步骤名称（type=rag_step时使用）")
    data: Optional[Dict[str, Any]] = Field(None, description="步骤数据或错误详情")
