"""文件夹相关的 Pydantic 模式。"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class FolderBase(BaseModel):
    """文件夹的基础模型。"""
    
    name: str = Field(..., min_length=1, max_length=200, description="文件夹名称")


class FolderCreate(FolderBase):
    """创建新文件夹的模型。"""
    
    parent_folder_id: Optional[str] = Field(None, description="父文件夹ID")


class FolderUpdate(BaseModel):
    """更新文件夹的模型。"""
    
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="文件夹名称")
    parent_folder_id: Optional[str] = Field(None, description="移动到的父文件夹ID")


class FolderResponse(FolderBase):
    """文件夹响应模型，包含元数据。"""
    
    id: str = Field(..., description="文件夹ID")
    knowledge_base_id: str = Field(..., description="所属知识库ID")
    parent_folder_id: Optional[str] = Field(None, description="父文件夹ID")
    user_id: str = Field(..., description="所属用户ID")
    path: str = Field(..., description="完整路径")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True


class FolderListResponse(BaseModel):
    """文件夹列表响应模型。"""
    
    items: list[FolderResponse] = Field(..., description="文件夹列表")
    total: int = Field(..., description="总数")
