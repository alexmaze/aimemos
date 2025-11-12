"""备忘录相关的 API 端点。"""

from fastapi import APIRouter, HTTPException, Query, Depends, status

from ....schemas.memo import (
    MemoCreate,
    MemoUpdate,
    MemoResponse,
    MemoListResponse,
)
from ....services.memo import get_memo_service
from ...dependencies import get_current_user

router = APIRouter()


@router.post("", response_model=MemoResponse, status_code=201, summary="创建备忘录")
async def create_memo(
    memo: MemoCreate,
    current_user: str = Depends(get_current_user)
):
    """创建新备忘录。
    
    需要认证。创建的备忘录会自动关联到当前登录用户。
    """
    memo_service = get_memo_service()
    return memo_service.create_memo(current_user, memo)


@router.get("", response_model=MemoListResponse, summary="列出备忘录")
async def list_memos(
    skip: int = Query(0, ge=0, description="跳过的数量"),
    limit: int = Query(100, ge=1, le=1000, description="返回的最大数量"),
    current_user: str = Depends(get_current_user)
):
    """列出所有备忘录，支持分页。
    
    需要认证。只返回当前用户的备忘录。
    """
    memo_service = get_memo_service()
    items, total = memo_service.list_memos(current_user, skip=skip, limit=limit)
    return MemoListResponse(items=items, total=total, skip=skip, limit=limit)


@router.get("/search", response_model=list[MemoResponse], summary="搜索备忘录")
async def search_memos(
    q: str = Query(..., min_length=1, description="搜索关键词"),
    current_user: str = Depends(get_current_user)
):
    """根据查询字符串搜索备忘录。
    
    需要认证。在标题、内容和标签中搜索匹配的备忘录。
    """
    memo_service = get_memo_service()
    return memo_service.search_memos(current_user, q)


@router.get("/{memo_id}", response_model=MemoResponse, summary="获取备忘录详情")
async def get_memo(
    memo_id: str,
    current_user: str = Depends(get_current_user)
):
    """根据 ID 获取指定备忘录。
    
    需要认证。只能获取当前用户的备忘录。
    """
    memo_service = get_memo_service()
    memo = memo_service.get_memo(current_user, memo_id)
    if not memo:
        raise HTTPException(status_code=404, detail="备忘录未找到")
    return memo


@router.put("/{memo_id}", response_model=MemoResponse, summary="更新备忘录")
async def update_memo(
    memo_id: str,
    memo_update: MemoUpdate,
    current_user: str = Depends(get_current_user)
):
    """更新指定备忘录。
    
    需要认证。只能更新当前用户的备忘录。
    """
    memo_service = get_memo_service()
    memo = memo_service.update_memo(current_user, memo_id, memo_update)
    if not memo:
        raise HTTPException(status_code=404, detail="备忘录未找到")
    return memo


@router.delete("/{memo_id}", status_code=204, summary="删除备忘录")
async def delete_memo(
    memo_id: str,
    current_user: str = Depends(get_current_user)
):
    """删除指定备忘录。
    
    需要认证。只能删除当前用户的备忘录。
    """
    memo_service = get_memo_service()
    if not memo_service.delete_memo(current_user, memo_id):
        raise HTTPException(status_code=404, detail="备忘录未找到")
