"""AI Memos 的 API 路由。"""

from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Depends, status

from .models import Memo, MemoCreate, MemoUpdate, MemoList
from .storage import get_storage, get_user_storage
from .auth import UserCreate, UserLogin, Token, create_access_token
from .dependencies import get_current_user
from .config import get_settings

router = APIRouter()


# 认证相关路由
@router.post("/auth/register", response_model=Token, status_code=201)
async def register(user_data: UserCreate):
    """用户注册。"""
    settings = get_settings()
    
    # 检查是否开启自动注册
    if not settings.enable_auto_registration:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="注册功能已关闭"
        )
    
    user_storage = get_user_storage()
    
    try:
        user = user_storage.create_user(user_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # 创建访问令牌
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.user_id},
        expires_delta=access_token_expires
    )
    
    return Token(access_token=access_token)


@router.post("/auth/login", response_model=Token)
async def login(user_data: UserLogin):
    """用户登录。"""
    settings = get_settings()
    user_storage = get_user_storage()
    
    user = user_storage.authenticate_user(user_data.user_id, user_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户ID或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 创建访问令牌
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.user_id},
        expires_delta=access_token_expires
    )
    
    return Token(access_token=access_token)


# 备忘录相关路由（需要认证）
@router.post("/memos", response_model=Memo, status_code=201)
async def create_memo(
    memo: MemoCreate,
    current_user: str = Depends(get_current_user)
):
    """创建新备忘录。"""
    storage = get_storage()
    return storage.create_memo(current_user, memo)


@router.get("/memos", response_model=MemoList)
async def list_memos(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: str = Depends(get_current_user)
):
    """列出所有备忘录，支持分页。"""
    storage = get_storage()
    items, total = storage.list_memos(current_user, skip=skip, limit=limit)
    return MemoList(items=items, total=total, skip=skip, limit=limit)


@router.get("/memos/search", response_model=list[Memo])
async def search_memos(
    q: str = Query(..., min_length=1),
    current_user: str = Depends(get_current_user)
):
    """根据查询字符串搜索备忘录。"""
    storage = get_storage()
    return storage.search_memos(current_user, q)


@router.get("/memos/{memo_id}", response_model=Memo)
async def get_memo(
    memo_id: str,
    current_user: str = Depends(get_current_user)
):
    """根据 ID 获取指定备忘录。"""
    storage = get_storage()
    memo = storage.get_memo(current_user, memo_id)
    if not memo:
        raise HTTPException(status_code=404, detail="备忘录未找到")
    return memo


@router.put("/memos/{memo_id}", response_model=Memo)
async def update_memo(
    memo_id: str,
    memo_update: MemoUpdate,
    current_user: str = Depends(get_current_user)
):
    """更新指定备忘录。"""
    storage = get_storage()
    memo = storage.update_memo(current_user, memo_id, memo_update)
    if not memo:
        raise HTTPException(status_code=404, detail="备忘录未找到")
    return memo


@router.delete("/memos/{memo_id}", status_code=204)
async def delete_memo(
    memo_id: str,
    current_user: str = Depends(get_current_user)
):
    """删除指定备忘录。"""
    storage = get_storage()
    if not storage.delete_memo(current_user, memo_id):
        raise HTTPException(status_code=404, detail="备忘录未找到")
