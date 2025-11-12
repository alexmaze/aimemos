"""AI Memos 的存储层。"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from .models import Memo, MemoCreate, MemoUpdate
from .auth import User, UserCreate, get_password_hash, verify_password


class UserStorage:
    """用户的内存存储。"""
    
    def __init__(self):
        """初始化用户存储。"""
        self._users: dict[str, User] = {}
    
    def create_user(self, user_data: UserCreate) -> User:
        """创建新用户。"""
        if user_data.user_id in self._users:
            raise ValueError("用户ID已存在")
        
        hashed_password = get_password_hash(user_data.password)
        user = User(
            user_id=user_data.user_id,
            hashed_password=hashed_password,
            created_at=datetime.utcnow(),
            is_active=True
        )
        
        self._users[user_data.user_id] = user
        return user
    
    def get_user(self, user_id: str) -> Optional[User]:
        """根据用户ID获取用户。"""
        return self._users.get(user_id)
    
    def authenticate_user(self, user_id: str, password: str) -> Optional[User]:
        """验证用户身份。"""
        user = self.get_user(user_id)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user


class MemoStorage:
    """备忘录的内存存储。"""
    
    def __init__(self):
        """初始化存储。"""
        # 按用户ID组织备忘录: {user_id: {memo_id: Memo}}
        self._memos: dict[str, dict[str, Memo]] = {}
    
    def _get_user_memos(self, user_id: str) -> dict[str, Memo]:
        """获取用户的备忘录字典。"""
        if user_id not in self._memos:
            self._memos[user_id] = {}
        return self._memos[user_id]
    
    def create_memo(self, user_id: str, memo_data: MemoCreate) -> Memo:
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
    
    def get_memo(self, user_id: str, memo_id: str) -> Optional[Memo]:
        """获取用户的指定备忘录。"""
        user_memos = self._get_user_memos(user_id)
        return user_memos.get(memo_id)
    
    def list_memos(self, user_id: str, skip: int = 0, limit: int = 100) -> tuple[list[Memo], int]:
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
    
    def update_memo(self, user_id: str, memo_id: str, memo_data: MemoUpdate) -> Optional[Memo]:
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
    
    def delete_memo(self, user_id: str, memo_id: str) -> bool:
        """删除用户的备忘录。"""
        user_memos = self._get_user_memos(user_id)
        if memo_id in user_memos:
            del user_memos[memo_id]
            return True
        return False
    
    def search_memos(self, user_id: str, query: str) -> list[Memo]:
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


# 全局存储实例
_user_storage: Optional[UserStorage] = None
_memo_storage: Optional[MemoStorage] = None


def get_user_storage() -> UserStorage:
    """获取或创建全局用户存储实例。"""
    global _user_storage
    if _user_storage is None:
        _user_storage = UserStorage()
    return _user_storage


def get_storage() -> MemoStorage:
    """获取或创建全局备忘录存储实例。"""
    global _memo_storage
    if _memo_storage is None:
        _memo_storage = MemoStorage()
    return _memo_storage
