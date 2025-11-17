"""API v1 路由聚合。"""

from fastapi import APIRouter

from .endpoints import auth, memos, knowledge_bases, documents, rag, chats

# 创建 v1 API 路由器
api_router = APIRouter()

# 注册子路由
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(memos.router, prefix="/memos", tags=["备忘录"])
api_router.include_router(knowledge_bases.router, prefix="/knowledge-bases", tags=["知识库"])
api_router.include_router(documents.router, prefix="/documents", tags=["文档"])
api_router.include_router(rag.router, prefix="/rag", tags=["RAG 搜索"])
api_router.include_router(chats.router, prefix="/chats", tags=["聊天会话"])
