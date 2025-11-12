"""备忘录相关的 Pydantic 模式。"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class MemoBase(BaseModel):
    """备忘录的基础模型。"""
    
    title: str = Field(..., min_length=1, max_length=200, description="标题")
    content: str = Field(..., min_length=1, description="内容")
    tags: list[str] = Field(default_factory=list, description="标签列表")


class MemoCreate(MemoBase):
    """创建新备忘录的模型。"""
    
    pass


class MemoUpdate(BaseModel):
    """更新备忘录的模型。"""
    
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="标题")
    content: Optional[str] = Field(None, min_length=1, description="内容")
    tags: Optional[list[str]] = Field(None, description="标签列表")


class MemoResponse(MemoBase):
    """备忘录响应模型，包含元数据。"""
    
    id: str = Field(..., description="备忘录ID")
    user_id: str = Field(..., description="所属用户ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True


class MemoListResponse(BaseModel):
    """备忘录列表响应模型，包含分页信息。"""
    
    items: list[MemoResponse] = Field(..., description="备忘录列表")
    total: int = Field(..., description="总数")
    skip: int = Field(..., description="跳过数量")
    limit: int = Field(..., description="限制数量")
