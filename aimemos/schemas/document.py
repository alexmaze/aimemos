"""文档相关的 Pydantic 模式。"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class DocumentBase(BaseModel):
    """文档的基础模型。"""
    
    name: str = Field(..., min_length=1, max_length=200, description="文档名称")
    summary: Optional[str] = Field(None, max_length=500, description="文档摘要")


class DocumentCreate(DocumentBase):
    """创建新笔记文档的模型。"""
    
    folder_id: Optional[str] = Field(None, description="所属文件夹ID")
    content: str = Field("", description="Markdown内容")


class FolderCreate(BaseModel):
    """创建新文件夹的模型。"""
    
    name: str = Field(..., min_length=1, max_length=200, description="文件夹名称")
    folder_id: Optional[str] = Field(None, description="父文件夹ID（folder_id表示父文件夹）")


class DocumentUpdate(BaseModel):
    """更新文档的模型。"""
    
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="文档名称")
    summary: Optional[str] = Field(None, max_length=500, description="文档摘要")
    content: Optional[str] = Field(None, description="内容（仅适用于笔记）")
    folder_id: Optional[str] = Field(None, description="移动到的文件夹ID")


class DocumentResponse(DocumentBase):
    """文档响应模型，包含元数据。"""
    
    id: str = Field(..., description="文档ID")
    knowledge_base_id: str = Field(..., description="所属知识库ID")
    folder_id: Optional[str] = Field(None, description="所属文件夹ID")
    user_id: str = Field(..., description="所属用户ID")
    doc_type: str = Field(..., description="文档类型: folder, note 或 uploaded")
    content: str = Field("", description="文档内容")
    
    # 文件夹特有字段
    path: Optional[str] = Field(None, description="文件夹路径（仅用于folder类型）")
    
    # 源文件信息（仅适用于上传文档）
    source_file_path: Optional[str] = Field(None, description="源文件路径")
    source_file_size: Optional[int] = Field(None, description="源文件大小（字节）")
    source_file_format: Optional[str] = Field(None, description="源文件格式")
    source_file_created_at: Optional[datetime] = Field(None, description="源文件创建时间")
    source_file_modified_at: Optional[datetime] = Field(None, description="源文件修改时间")
    
    # RAG 索引状态字段
    rag_index_status: Optional[str] = Field(None, description="RAG 索引状态: pending, indexing, completed, failed, timeout")
    rag_index_started_at: Optional[datetime] = Field(None, description="索引开始时间")
    rag_index_completed_at: Optional[datetime] = Field(None, description="索引完成时间")
    rag_index_error: Optional[str] = Field(None, description="索引错误信息（如果失败）")
    
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """文档列表响应模型，包含分页信息。"""
    
    items: list[DocumentResponse] = Field(..., description="文档列表（包含文件夹和文件）")
    total: int = Field(..., description="总数")
    skip: int = Field(..., description="跳过数量")
    limit: int = Field(..., description="限制数量")
