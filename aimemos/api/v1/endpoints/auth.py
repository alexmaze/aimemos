"""认证相关的 API 端点。"""

from datetime import timedelta
from fastapi import APIRouter, HTTPException, status

from ....schemas.user import UserCreate, UserLogin, Token
from ....services.auth import create_access_token
from ....db import get_user_repository
from ....config import get_settings

router = APIRouter()


@router.post("/register", response_model=Token, status_code=201, summary="用户注册")
async def register(user_data: UserCreate):
    """用户注册。
    
    如果开启了自动注册功能，用户可以通过此接口注册新账号。
    注册成功后会自动返回访问令牌。
    """
    settings = get_settings()
    
    # 检查是否开启自动注册
    if not settings.enable_auto_registration:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="注册功能已关闭"
        )
    
    user_repository = get_user_repository()
    
    try:
        user = user_repository.create(user_data)
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


@router.post("/login", response_model=Token, summary="用户登录")
async def login(user_data: UserLogin):
    """用户登录。
    
    验证用户凭据后返回 JWT 访问令牌。
    令牌应在后续请求的 Authorization header 中使用。
    """
    settings = get_settings()
    user_repository = get_user_repository()
    
    user = user_repository.authenticate(user_data.user_id, user_data.password)
    
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
