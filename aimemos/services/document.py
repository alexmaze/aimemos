"""文档业务逻辑服务。"""

import os
import re
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional
from fastapi import UploadFile

from ..models.document import Document
from ..schemas.document import DocumentCreate, DocumentUpdate
from ..db import get_document_repository, get_knowledge_base_repository
from ..config import get_settings
from .file_handler import FileHandler


def sanitize_path_component(component: str) -> str:
    """Sanitize a path component to prevent path traversal attacks.
    
    Args:
        component: The path component to sanitize
        
    Returns:
        A safe path component
    """
    # Remove any path separators and parent directory references
    safe_component = re.sub(r'[/\\]', '', component)
    safe_component = re.sub(r'\.\.', '', safe_component)
    # Remove any control characters
    safe_component = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', safe_component)
    return safe_component


class DocumentService:
    """文档业务逻辑服务。"""
    
    def __init__(self):
        """初始化服务。"""
        self.repository = get_document_repository()
        self.kb_repository = get_knowledge_base_repository()
        self.settings = get_settings()
        self.file_handler = FileHandler()
    
    def create_note(
        self, 
        user_id: str, 
        kb_id: str, 
        doc_data: DocumentCreate
    ) -> Document:
        """创建新笔记文档。
        
        Args:
            user_id: 用户ID
            kb_id: 知识库ID
            doc_data: 文档数据
            
        Returns:
            创建的文档
        """
        # 验证知识库存在
        kb = self.kb_repository.get_by_id(user_id, kb_id)
        if not kb:
            raise ValueError("知识库不存在")
        
        return self.repository.create_note(user_id, kb_id, doc_data)
    
    def create_folder(
        self,
        user_id: str,
        kb_id: str,
        name: str,
        parent_folder_id: Optional[str] = None
    ) -> Document:
        """创建文件夹。
        
        Args:
            user_id: 用户ID
            kb_id: 知识库ID
            name: 文件夹名称
            parent_folder_id: 父文件夹ID
            
        Returns:
            创建的文件夹
        """
        # 验证知识库存在
        kb = self.kb_repository.get_by_id(user_id, kb_id)
        if not kb:
            raise ValueError("知识库不存在")
        
        return self.repository.create_folder(user_id, kb_id, name, parent_folder_id)
    
    def upload_document(
        self,
        user_id: str,
        kb_id: str,
        file: UploadFile,
        folder_id: Optional[str] = None,
        summary: Optional[str] = None
    ) -> Document:
        """上传文档到知识库。
        
        Args:
            user_id: 用户ID
            kb_id: 知识库ID
            file: 上传的文件
            folder_id: 文件夹ID
            summary: 文档摘要
            
        Returns:
            创建的文档
            
        Raises:
            ValueError: 文件格式不支持或其他错误
        """
        # 验证知识库存在
        kb = self.kb_repository.get_by_id(user_id, kb_id)
        if not kb:
            raise ValueError("知识库不存在")
        
        # 检查文件格式
        if not self.file_handler.is_supported_format(file.filename):
            raise ValueError(f"不支持的文件格式: {file.filename}")
        
        # 确定存储路径 - 使用安全的路径组件
        storage_root = Path(self.settings.storage_root).resolve()
        safe_user_id = sanitize_path_component(user_id)
        safe_kb_id = sanitize_path_component(kb_id)
        kb_dir = storage_root / safe_user_id / safe_kb_id
        
        # 如果有文件夹，按文件夹路径组织
        if folder_id:
            safe_folder_id = sanitize_path_component(folder_id)
            kb_dir = kb_dir / safe_folder_id
        
        # 确保目录在storage_root之内（防止路径遍历）
        kb_dir = kb_dir.resolve()
        if not str(kb_dir).startswith(str(storage_root)):
            raise ValueError("无效的存储路径")
        
        kb_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成唯一的文件名（保留原始扩展名）- 清理文件名
        file_format = self.file_handler.get_file_format(file.filename)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        safe_original_name = sanitize_path_component(file.filename)
        safe_filename = f"{timestamp}_{safe_original_name}"
        file_path = kb_dir / safe_filename
        
        # 再次验证最终路径在storage_root内
        file_path = file_path.resolve()
        if not str(file_path).startswith(str(storage_root)):
            raise ValueError("无效的文件路径")
        
        # 保存文件
        try:
            with open(file_path, 'wb') as f:
                shutil.copyfileobj(file.file, f)
        finally:
            file.file.close()
        
        # 获取文件信息
        file_stat = os.stat(file_path)
        file_size = file_stat.st_size
        file_created_at = datetime.fromtimestamp(file_stat.st_ctime)
        file_modified_at = datetime.fromtimestamp(file_stat.st_mtime)
        
        # 提取文本内容
        try:
            text_content = self.file_handler.extract_text(str(file_path))
        except Exception as e:
            # 如果提取失败，删除文件并抛出错误
            os.remove(file_path)
            raise ValueError(f"无法提取文件内容: {str(e)}")
        
        # 计算相对路径
        relative_path = str(file_path.relative_to(storage_root))
        
        # 创建文档记录
        return self.repository.create_uploaded(
            user_id=user_id,
            kb_id=kb_id,
            name=file.filename,
            folder_id=folder_id,
            content=text_content,
            source_file_path=relative_path,
            source_file_size=file_size,
            source_file_format=file_format,
            source_file_created_at=file_created_at,
            source_file_modified_at=file_modified_at,
            summary=summary
        )
    
    def get_document(self, user_id: str, doc_id: str) -> Optional[Document]:
        """获取文档。
        
        Args:
            user_id: 用户ID
            doc_id: 文档ID
            
        Returns:
            文档，如果不存在则返回 None
        """
        return self.repository.get_by_id(user_id, doc_id)
    
    def list_documents(
        self, 
        user_id: str, 
        kb_id: str,
        folder_id: Optional[str] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> tuple[list[Document], int]:
        """列出知识库中的文档。
        
        Args:
            user_id: 用户ID
            kb_id: 知识库ID
            folder_id: 文件夹ID（可选）
            skip: 跳过数量
            limit: 限制数量
            
        Returns:
            (文档列表, 总数)
        """
        return self.repository.list_by_kb(user_id, kb_id, folder_id, skip, limit)
    
    def update_document(
        self, 
        user_id: str, 
        doc_id: str, 
        doc_data: DocumentUpdate
    ) -> Optional[Document]:
        """更新文档。
        
        Args:
            user_id: 用户ID
            doc_id: 文档ID
            doc_data: 更新数据
            
        Returns:
            更新后的文档，如果不存在则返回 None
        """
        return self.repository.update(user_id, doc_id, doc_data)
    
    def delete_document(self, user_id: str, doc_id: str) -> bool:
        """删除文档。
        
        Args:
            user_id: 用户ID
            doc_id: 文档ID
            
        Returns:
            是否删除成功
        """
        # 获取文档信息
        doc = self.repository.get_by_id(user_id, doc_id)
        if not doc:
            return False
        
        # 如果是上传文档，删除源文件
        if doc.doc_type == 'uploaded' and doc.source_file_path:
            storage_root = Path(self.settings.storage_root).resolve()
            file_path = (storage_root / doc.source_file_path).resolve()
            
            # 确保文件路径在storage_root之内（防止路径遍历）
            if str(file_path).startswith(str(storage_root)) and file_path.exists():
                try:
                    os.remove(file_path)
                except Exception:
                    # 忽略删除文件时的错误
                    pass
        
        return self.repository.delete(user_id, doc_id)
    
    def search_documents(
        self, 
        user_id: str, 
        kb_id: str, 
        query: str
    ) -> list[Document]:
        """搜索文档。
        
        Args:
            user_id: 用户ID
            kb_id: 知识库ID
            query: 搜索查询
            
        Returns:
            匹配的文档列表
        """
        return self.repository.search(user_id, kb_id, query)


def get_document_service() -> DocumentService:
    """获取文档服务实例。"""
    return DocumentService()
