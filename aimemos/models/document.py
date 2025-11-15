"""文档领域模型。"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class Document(BaseModel):
    """文档领域模型。
    
    支持三种类型：
    - 'folder': 文件夹（特殊类型的文档）
    - 'note': 笔记文档
    - 'uploaded': 上传的文档
    """
    
    id: str
    knowledge_base_id: str
    folder_id: Optional[str] = None  # 所属文件夹ID，None表示在根目录
    user_id: str
    name: str
    doc_type: str  # 'folder', 'note', 或 'uploaded'
    summary: Optional[str] = None
    content: str = ""  # 对于笔记是markdown内容，对于上传文档是提取的纯文本，对于文件夹为空
    
    # 文件夹特有字段
    path: Optional[str] = None  # 完整路径，如 '/folder1/folder2'，仅用于文件夹类型
    
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
