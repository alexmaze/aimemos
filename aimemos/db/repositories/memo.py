"""备忘录数据访问仓储。"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from ...models.memo import Memo
from ...schemas.memo import MemoCreate, MemoUpdate


class MemoRepository:
    """备忘录数据访问仓储。"""
    
    def __init__(self):
        """初始化备忘录仓储。"""
        # 按用户ID组织备忘录: {user_id: {memo_id: Memo}}
        self._memos: dict[str, dict[str, Memo]] = {}
    
    def _get_user_memos(self, user_id: str) -> dict[str, Memo]:
        """获取用户的备忘录字典。"""
        if user_id not in self._memos:
            self._memos[user_id] = {}
        return self._memos[user_id]
    
    def create(self, user_id: str, memo_data: MemoCreate) -> Memo:
        """为指定用户创建新备忘录。"""
        memo_id = str(uuid4())
        now = datetime.utcnow()
        
        memo = Memo(
            id=memo_id,
            user_id=user_id,
            title=memo_data.title,
            content=memo_data.content,
            tags=memo_data.tags,
            created_at=now,
            updated_at=now,
        )
        
        user_memos = self._get_user_memos(user_id)
        user_memos[memo_id] = memo
        return memo
    
    def get_by_id(self, user_id: str, memo_id: str) -> Optional[Memo]:
        """获取用户的指定备忘录。"""
        user_memos = self._get_user_memos(user_id)
        return user_memos.get(memo_id)
    
    def list_by_user(
        self, 
        user_id: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> tuple[list[Memo], int]:
        """列出用户的备忘录，支持分页。"""
        user_memos = self._get_user_memos(user_id)
        all_memos = sorted(
            user_memos.values(),
            key=lambda m: m.created_at,
            reverse=True
        )
        total = len(all_memos)
        items = all_memos[skip:skip + limit]
        return items, total
    
    def update(
        self, 
        user_id: str, 
        memo_id: str, 
        memo_data: MemoUpdate
    ) -> Optional[Memo]:
        """更新用户的备忘录。"""
        user_memos = self._get_user_memos(user_id)
        memo = user_memos.get(memo_id)
        if not memo:
            return None
        
        update_dict = memo_data.model_dump(exclude_unset=True)
        updated_memo = memo.model_copy(
            update={
                **update_dict,
                "updated_at": datetime.utcnow()
            }
        )
        
        user_memos[memo_id] = updated_memo
        return updated_memo
    
    def delete(self, user_id: str, memo_id: str) -> bool:
        """删除用户的备忘录。"""
        user_memos = self._get_user_memos(user_id)
        if memo_id in user_memos:
            del user_memos[memo_id]
            return True
        return False
    
    def search(self, user_id: str, query: str) -> list[Memo]:
        """搜索用户的备忘录。"""
        user_memos = self._get_user_memos(user_id)
        query_lower = query.lower()
        results = [
            memo for memo in user_memos.values()
            if query_lower in memo.title.lower() or 
               query_lower in memo.content.lower() or
               any(query_lower in tag.lower() for tag in memo.tags)
        ]
        return sorted(results, key=lambda m: m.created_at, reverse=True)
