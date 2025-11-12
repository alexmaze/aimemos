"""备忘录业务逻辑服务。"""

from typing import Optional

from ..models.memo import Memo
from ..schemas.memo import MemoCreate, MemoUpdate
from ..db import get_memo_repository


class MemoService:
    """备忘录业务逻辑服务。"""
    
    def __init__(self):
        """初始化服务。"""
        self.repository = get_memo_repository()
    
    def create_memo(self, user_id: str, memo_data: MemoCreate) -> Memo:
        """创建新备忘录。
        
        Args:
            user_id: 用户ID
            memo_data: 备忘录数据
            
        Returns:
            创建的备忘录
        """
        return self.repository.create(user_id, memo_data)
    
    def get_memo(self, user_id: str, memo_id: str) -> Optional[Memo]:
        """获取备忘录。
        
        Args:
            user_id: 用户ID
            memo_id: 备忘录ID
            
        Returns:
            备忘录，如果不存在则返回 None
        """
        return self.repository.get_by_id(user_id, memo_id)
    
    def list_memos(
        self, 
        user_id: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> tuple[list[Memo], int]:
        """列出用户的备忘录。
        
        Args:
            user_id: 用户ID
            skip: 跳过数量
            limit: 限制数量
            
        Returns:
            (备忘录列表, 总数)
        """
        return self.repository.list_by_user(user_id, skip, limit)
    
    def update_memo(
        self, 
        user_id: str, 
        memo_id: str, 
        memo_data: MemoUpdate
    ) -> Optional[Memo]:
        """更新备忘录。
        
        Args:
            user_id: 用户ID
            memo_id: 备忘录ID
            memo_data: 更新数据
            
        Returns:
            更新后的备忘录，如果不存在则返回 None
        """
        return self.repository.update(user_id, memo_id, memo_data)
    
    def delete_memo(self, user_id: str, memo_id: str) -> bool:
        """删除备忘录。
        
        Args:
            user_id: 用户ID
            memo_id: 备忘录ID
            
        Returns:
            是否删除成功
        """
        return self.repository.delete(user_id, memo_id)
    
    def search_memos(self, user_id: str, query: str) -> list[Memo]:
        """搜索备忘录。
        
        Args:
            user_id: 用户ID
            query: 搜索查询
            
        Returns:
            匹配的备忘录列表
        """
        return self.repository.search(user_id, query)


def get_memo_service() -> MemoService:
    """获取备忘录服务实例。"""
    return MemoService()
