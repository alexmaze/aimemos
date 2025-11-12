"""备忘录领域模型。"""

from datetime import datetime
from pydantic import BaseModel, Field


class Memo(BaseModel):
    """备忘录领域模型。"""
    
    id: str
    user_id: str
    title: str
    content: str
    tags: list[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
