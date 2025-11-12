"""AI Memos 的数据模型。"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class MemoBase(BaseModel):
    """备忘录的基础模型。"""
    
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    tags: list[str] = Field(default_factory=list)


class MemoCreate(MemoBase):
    """创建新备忘录的模型。"""
    
    pass


class MemoUpdate(BaseModel):
    """更新备忘录的模型。"""
    
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    tags: Optional[list[str]] = None


class Memo(MemoBase):
    """完整的备忘录模型，包含元数据。"""
    
    id: str
    user_id: str  # 所属用户ID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class MemoList(BaseModel):
    """备忘录列表及分页信息。"""
    
    items: list[Memo]
    total: int
    skip: int
    limit: int
