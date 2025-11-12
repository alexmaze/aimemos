"""文件夹领域模型。"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class Folder(BaseModel):
    """文件夹领域模型。"""
    
    id: str
    knowledge_base_id: str
    parent_folder_id: Optional[str] = None  # 父文件夹ID，None表示在根目录
    user_id: str
    name: str
    path: str  # 完整路径，如 '/folder1/folder2'
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
