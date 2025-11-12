"""用户领域模型。"""

from datetime import datetime
from pydantic import BaseModel, Field


class User(BaseModel):
    """用户领域模型。"""
    
    user_id: str
    hashed_password: str
    created_at: datetime
    is_active: bool = True
    
    class Config:
        from_attributes = True
