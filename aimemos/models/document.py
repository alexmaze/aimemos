"""文档领域模型。"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class Document(BaseModel):
    """文档领域模型。"""
    
    id: str
    knowledge_base_id: str
    folder_id: Optional[str] = None  # 所属文件夹ID，None表示在根目录
    user_id: str
    name: str
    doc_type: str  # 'uploaded' 或 'note'
    summary: Optional[str] = None
    content: str  # 对于笔记是markdown内容，对于上传文档是提取的纯文本
    
    # 源文件信息（仅适用于上传文档）
    source_file_path: Optional[str] = None  # 相对于storage_root的路径
    source_file_size: Optional[int] = None  # 字节
    source_file_format: Optional[str] = None  # 文件扩展名，如 'pdf', 'docx'
    source_file_created_at: Optional[datetime] = None
    source_file_modified_at: Optional[datetime] = None
    
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
