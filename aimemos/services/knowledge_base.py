"""知识库业务逻辑服务。"""

from typing import Optional

from ..models.knowledge_base import KnowledgeBase
from ..schemas.knowledge_base import KnowledgeBaseCreate, KnowledgeBaseUpdate
from ..db import get_knowledge_base_repository


class KnowledgeBaseService:
    """知识库业务逻辑服务。"""
    
    def __init__(self):
        """初始化服务。"""
        self.repository = get_knowledge_base_repository()
    
    def create_knowledge_base(
        self, 
        user_id: str, 
        kb_data: KnowledgeBaseCreate
    ) -> KnowledgeBase:
        """创建新知识库。
        
        Args:
            user_id: 用户ID
            kb_data: 知识库数据
            
        Returns:
            创建的知识库
        """
        return self.repository.create(user_id, kb_data)
    
    def get_knowledge_base(
        self, 
        user_id: str, 
        kb_id: str
    ) -> Optional[KnowledgeBase]:
        """获取知识库。
        
        Args:
            user_id: 用户ID
            kb_id: 知识库ID
            
        Returns:
            知识库，如果不存在则返回 None
        """
        return self.repository.get_by_id(user_id, kb_id)
    
    def list_knowledge_bases(
        self, 
        user_id: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> tuple[list[KnowledgeBase], int]:
        """列出用户的知识库。
        
        Args:
            user_id: 用户ID
            skip: 跳过数量
            limit: 限制数量
            
        Returns:
            (知识库列表, 总数)
        """
        return self.repository.list_by_user(user_id, skip, limit)
    
    def update_knowledge_base(
        self, 
        user_id: str, 
        kb_id: str, 
        kb_data: KnowledgeBaseUpdate
    ) -> Optional[KnowledgeBase]:
        """更新知识库。
        
        Args:
            user_id: 用户ID
            kb_id: 知识库ID
            kb_data: 更新数据
            
        Returns:
            更新后的知识库，如果不存在则返回 None
        """
        return self.repository.update(user_id, kb_id, kb_data)
    
    def delete_knowledge_base(self, user_id: str, kb_id: str) -> bool:
        """删除知识库。
        
        Args:
            user_id: 用户ID
            kb_id: 知识库ID
            
        Returns:
            是否删除成功
        """
        return self.repository.delete(user_id, kb_id)


def get_knowledge_base_service() -> KnowledgeBaseService:
    """获取知识库服务实例。"""
    return KnowledgeBaseService()
