"""知识库相关的 Pydantic 模式。"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class KnowledgeBaseBase(BaseModel):
    """知识库的基础模型。"""
    
    name: str = Field(..., min_length=1, max_length=200, description="知识库名称")
    description: Optional[str] = Field(None, max_length=1000, description="知识库简介")
    cover_image: Optional[str] = Field(None, description="封面图片路径")


class KnowledgeBaseCreate(KnowledgeBaseBase):
    """创建新知识库的模型。"""
    
    pass


class KnowledgeBaseUpdate(BaseModel):
    """更新知识库的模型。"""
    
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="知识库名称")
    description: Optional[str] = Field(None, max_length=1000, description="知识库简介")
    cover_image: Optional[str] = Field(None, description="封面图片路径")


class KnowledgeBaseResponse(KnowledgeBaseBase):
    """知识库响应模型，包含元数据。"""
    
    id: str = Field(..., description="知识库ID")
    user_id: str = Field(..., description="所属用户ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True


class KnowledgeBaseListResponse(BaseModel):
    """知识库列表响应模型，包含分页信息。"""
    
    items: list[KnowledgeBaseResponse] = Field(..., description="知识库列表")
    total: int = Field(..., description="总数")
    skip: int = Field(..., description="跳过数量")
    limit: int = Field(..., description="限制数量")
