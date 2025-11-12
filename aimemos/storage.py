"""AI Memos 的存储层。"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from .models import Memo, MemoCreate, MemoUpdate


class MemoStorage:
    """备忘录的内存存储。"""
    
    def __init__(self):
        """初始化存储。"""
        self._memos: dict[str, Memo] = {}
    
    def create_memo(self, memo_data: MemoCreate) -> Memo:
        """创建新备忘录。"""
        memo_id = str(uuid4())
        now = datetime.utcnow()
        
        memo = Memo(
            id=memo_id,
            title=memo_data.title,
            content=memo_data.content,
            tags=memo_data.tags,
            created_at=now,
            updated_at=now,
        )
        
        self._memos[memo_id] = memo
        return memo
    
    def get_memo(self, memo_id: str) -> Optional[Memo]:
        """根据 ID 获取备忘录。"""
        return self._memos.get(memo_id)
    
    def list_memos(self, skip: int = 0, limit: int = 100) -> tuple[list[Memo], int]:
        """列出备忘录，支持分页。"""
        all_memos = sorted(
            self._memos.values(),
            key=lambda m: m.created_at,
            reverse=True
        )
        total = len(all_memos)
        items = all_memos[skip:skip + limit]
        return items, total
    
    def update_memo(self, memo_id: str, memo_data: MemoUpdate) -> Optional[Memo]:
        """更新备忘录。"""
        memo = self._memos.get(memo_id)
        if not memo:
            return None
        
        update_dict = memo_data.model_dump(exclude_unset=True)
        updated_memo = memo.model_copy(
            update={
                **update_dict,
                "updated_at": datetime.utcnow()
            }
        )
        
        self._memos[memo_id] = updated_memo
        return updated_memo
    
    def delete_memo(self, memo_id: str) -> bool:
        """删除备忘录。"""
        if memo_id in self._memos:
            del self._memos[memo_id]
            return True
        return False
    
    def search_memos(self, query: str) -> list[Memo]:
        """根据查询字符串搜索备忘录。"""
        query_lower = query.lower()
        results = [
            memo for memo in self._memos.values()
            if query_lower in memo.title.lower() or 
               query_lower in memo.content.lower() or
               any(query_lower in tag.lower() for tag in memo.tags)
        ]
        return sorted(results, key=lambda m: m.created_at, reverse=True)


# 全局存储实例
_storage: Optional[MemoStorage] = None


def get_storage() -> MemoStorage:
    """获取或创建全局存储实例。"""
    global _storage
    if _storage is None:
        _storage = MemoStorage()
    return _storage
