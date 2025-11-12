"""数据库存储管理。"""

from typing import Optional

from .repositories import UserRepository, MemoRepository


# 全局仓储实例
_user_repository: Optional[UserRepository] = None
_memo_repository: Optional[MemoRepository] = None


def get_user_repository() -> UserRepository:
    """获取或创建全局用户仓储实例。"""
    global _user_repository
    if _user_repository is None:
        _user_repository = UserRepository()
    return _user_repository


def get_memo_repository() -> MemoRepository:
    """获取或创建全局备忘录仓储实例。"""
    global _memo_repository
    if _memo_repository is None:
        _memo_repository = MemoRepository()
    return _memo_repository
