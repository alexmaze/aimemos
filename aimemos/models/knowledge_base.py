"""知识库领域模型。"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class KnowledgeBase(BaseModel):
    """知识库领域模型。"""
    
    id: str
    user_id: str
    name: str
    description: Optional[str] = None
    cover_image: Optional[str] = None  # 封面图片路径
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
