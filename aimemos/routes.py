"""AI Memos 的 API 路由。"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from .models import Memo, MemoCreate, MemoUpdate, MemoList
from .storage import get_storage

router = APIRouter()


@router.post("/memos", response_model=Memo, status_code=201)
async def create_memo(memo: MemoCreate):
    """创建新备忘录。"""
    storage = get_storage()
    return storage.create_memo(memo)


@router.get("/memos", response_model=MemoList)
async def list_memos(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """列出所有备忘录，支持分页。"""
    storage = get_storage()
    items, total = storage.list_memos(skip=skip, limit=limit)
    return MemoList(items=items, total=total, skip=skip, limit=limit)


@router.get("/memos/search", response_model=list[Memo])
async def search_memos(q: str = Query(..., min_length=1)):
    """根据查询字符串搜索备忘录。"""
    storage = get_storage()
    return storage.search_memos(q)


@router.get("/memos/{memo_id}", response_model=Memo)
async def get_memo(memo_id: str):
    """根据 ID 获取指定备忘录。"""
    storage = get_storage()
    memo = storage.get_memo(memo_id)
    if not memo:
        raise HTTPException(status_code=404, detail="备忘录未找到")
    return memo


@router.put("/memos/{memo_id}", response_model=Memo)
async def update_memo(memo_id: str, memo_update: MemoUpdate):
    """更新指定备忘录。"""
    storage = get_storage()
    memo = storage.update_memo(memo_id, memo_update)
    if not memo:
        raise HTTPException(status_code=404, detail="备忘录未找到")
    return memo


@router.delete("/memos/{memo_id}", status_code=204)
async def delete_memo(memo_id: str):
    """删除指定备忘录。"""
    storage = get_storage()
    if not storage.delete_memo(memo_id):
        raise HTTPException(status_code=404, detail="备忘录未找到")
