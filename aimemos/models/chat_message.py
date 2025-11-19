"""聊天消息领域模型。"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ChatMessage(BaseModel):
    """聊天消息领域模型。
    
    代表会话中的一条消息，可以是用户消息或AI助手消息。
    一条消息可以同时包含思考过程和正文内容。
    """
    
    id: str  # 消息ID (UUID)
    session_id: str  # 所属会话ID
    role: str  # 'user' 或 'assistant'
    thinking_process: Optional[str] = None  # 思考过程（如果有）
    content: str  # 消息正文内容
    
    # RAG相关字段
    rag_context: Optional[str] = None  # RAG检索到的上下文
    rag_sources: Optional[str] = None  # RAG来源信息（JSON格式）
    
    created_at: datetime
    
    class Config:
        from_attributes = True
