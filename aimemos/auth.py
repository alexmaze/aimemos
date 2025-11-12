"""用户认证相关功能。"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field

from .config import get_settings

# 密码加密上下文 - 使用 sha256 避免 bcrypt 版本问题
pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")


class User(BaseModel):
    """用户模型。"""
    
    user_id: str = Field(..., min_length=3, max_length=50)
    hashed_password: str
    created_at: datetime
    is_active: bool = True


class UserCreate(BaseModel):
    """创建用户的模型。"""
    
    user_id: str = Field(..., min_length=3, max_length=50, description="用户ID")
    password: str = Field(..., min_length=6, description="密码")


class UserLogin(BaseModel):
    """用户登录的模型。"""
    
    user_id: str = Field(..., description="用户ID")
    password: str = Field(..., description="密码")


class Token(BaseModel):
    """访问令牌模型。"""
    
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """令牌数据模型。"""
    
    user_id: Optional[str] = None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码。"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """获取密码哈希值。"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌。"""
    settings = get_settings()
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def verify_token(token: str) -> Optional[str]:
    """验证令牌并返回用户ID。"""
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        return user_id
    except JWTError:
        return None
