"""文件夹业务逻辑服务。"""

from typing import Optional

from ..models.folder import Folder
from ..schemas.folder import FolderCreate, FolderUpdate
from ..db import get_folder_repository, get_knowledge_base_repository


class FolderService:
    """文件夹业务逻辑服务。"""
    
    def __init__(self):
        """初始化服务。"""
        self.repository = get_folder_repository()
        self.kb_repository = get_knowledge_base_repository()
    
    def create_folder(
        self, 
        user_id: str, 
        kb_id: str, 
        folder_data: FolderCreate
    ) -> Folder:
        """创建新文件夹。
        
        Args:
            user_id: 用户ID
            kb_id: 知识库ID
            folder_data: 文件夹数据
            
        Returns:
            创建的文件夹
        """
        # 验证知识库存在
        kb = self.kb_repository.get_by_id(user_id, kb_id)
        if not kb:
            raise ValueError("知识库不存在")
        
        return self.repository.create(user_id, kb_id, folder_data)
    
    def get_folder(self, user_id: str, folder_id: str) -> Optional[Folder]:
        """获取文件夹。
        
        Args:
            user_id: 用户ID
            folder_id: 文件夹ID
            
        Returns:
            文件夹，如果不存在则返回 None
        """
        return self.repository.get_by_id(user_id, folder_id)
    
    def list_folders(
        self, 
        user_id: str, 
        kb_id: str,
        parent_folder_id: Optional[str] = None
    ) -> tuple[list[Folder], int]:
        """列出知识库中的文件夹。
        
        Args:
            user_id: 用户ID
            kb_id: 知识库ID
            parent_folder_id: 父文件夹ID（可选）
            
        Returns:
            (文件夹列表, 总数)
        """
        return self.repository.list_by_kb(user_id, kb_id, parent_folder_id)
    
    def update_folder(
        self, 
        user_id: str, 
        folder_id: str, 
        folder_data: FolderUpdate
    ) -> Optional[Folder]:
        """更新文件夹。
        
        Args:
            user_id: 用户ID
            folder_id: 文件夹ID
            folder_data: 更新数据
            
        Returns:
            更新后的文件夹，如果不存在则返回 None
        """
        return self.repository.update(user_id, folder_id, folder_data)
    
    def delete_folder(self, user_id: str, folder_id: str) -> bool:
        """删除文件夹。
        
        Args:
            user_id: 用户ID
            folder_id: 文件夹ID
            
        Returns:
            是否删除成功
        """
        return self.repository.delete(user_id, folder_id)


def get_folder_service() -> FolderService:
    """获取文件夹服务实例。"""
    return FolderService()
