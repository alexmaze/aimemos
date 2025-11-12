"""数据库存储管理。"""

from typing import Optional

from .repositories import (
    UserRepository,
    MemoRepository,
    KnowledgeBaseRepository,
    DocumentRepository,
)


# 全局仓储实例
_user_repository: Optional[UserRepository] = None
_memo_repository: Optional[MemoRepository] = None
_knowledge_base_repository: Optional[KnowledgeBaseRepository] = None
_document_repository: Optional[DocumentRepository] = None


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


def get_knowledge_base_repository() -> KnowledgeBaseRepository:
    """获取或创建全局知识库仓储实例。"""
    global _knowledge_base_repository
    if _knowledge_base_repository is None:
        _knowledge_base_repository = KnowledgeBaseRepository()
    return _knowledge_base_repository


def get_document_repository() -> DocumentRepository:
    """获取或创建全局文档仓储实例。"""
    global _document_repository
    if _document_repository is None:
        _document_repository = DocumentRepository()
    return _document_repository
