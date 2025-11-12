"""知识库相关的 API 端点。"""

from fastapi import APIRouter, HTTPException, Query, Depends, status

from ....schemas.knowledge_base import (
    KnowledgeBaseCreate,
    KnowledgeBaseUpdate,
    KnowledgeBaseResponse,
    KnowledgeBaseListResponse,
)
from ....services.knowledge_base import get_knowledge_base_service
from ...dependencies import get_current_user

router = APIRouter()


@router.post("", response_model=KnowledgeBaseResponse, status_code=201, summary="创建知识库")
async def create_knowledge_base(
    kb: KnowledgeBaseCreate,
    current_user: str = Depends(get_current_user)
):
    """创建新知识库。
    
    需要认证。创建的知识库会自动关联到当前登录用户。
    """
    kb_service = get_knowledge_base_service()
    return kb_service.create_knowledge_base(current_user, kb)


@router.get("", response_model=KnowledgeBaseListResponse, summary="列出知识库")
async def list_knowledge_bases(
    skip: int = Query(0, ge=0, description="跳过的数量"),
    limit: int = Query(100, ge=1, le=1000, description="返回的最大数量"),
    current_user: str = Depends(get_current_user)
):
    """列出所有知识库，支持分页。
    
    需要认证。只返回当前用户的知识库。
    """
    kb_service = get_knowledge_base_service()
    items, total = kb_service.list_knowledge_bases(current_user, skip=skip, limit=limit)
    return KnowledgeBaseListResponse(items=items, total=total, skip=skip, limit=limit)


@router.get("/{kb_id}", response_model=KnowledgeBaseResponse, summary="获取知识库详情")
async def get_knowledge_base(
    kb_id: str,
    current_user: str = Depends(get_current_user)
):
    """根据 ID 获取指定知识库。
    
    需要认证。只能获取当前用户的知识库。
    """
    kb_service = get_knowledge_base_service()
    kb = kb_service.get_knowledge_base(current_user, kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="知识库未找到")
    return kb


@router.put("/{kb_id}", response_model=KnowledgeBaseResponse, summary="更新知识库")
async def update_knowledge_base(
    kb_id: str,
    kb_update: KnowledgeBaseUpdate,
    current_user: str = Depends(get_current_user)
):
    """更新指定知识库。
    
    需要认证。只能更新当前用户的知识库。
    """
    kb_service = get_knowledge_base_service()
    kb = kb_service.update_knowledge_base(current_user, kb_id, kb_update)
    if not kb:
        raise HTTPException(status_code=404, detail="知识库未找到")
    return kb


@router.delete("/{kb_id}", status_code=204, summary="删除知识库")
async def delete_knowledge_base(
    kb_id: str,
    current_user: str = Depends(get_current_user)
):
    """删除指定知识库。
    
    需要认证。只能删除当前用户的知识库。
    """
    kb_service = get_knowledge_base_service()
    if not kb_service.delete_knowledge_base(current_user, kb_id):
        raise HTTPException(status_code=404, detail="知识库未找到")
