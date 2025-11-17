"""聊天会话领域模型。"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ChatSession(BaseModel):
    """聊天会话领域模型。
    
    代表用户与AI助手的一次对话会话。
    """
    
    id: str  # 会话ID (UUID)
    user_id: str  # 所属用户ID
    title: str  # 会话标题
    knowledge_base_id: Optional[str] = None  # 关联的知识库ID（可选，用于RAG）
    
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
