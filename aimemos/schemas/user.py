"""用户相关的 Pydantic 模式。"""

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    """创建用户的请求模型。"""
    
    user_id: str = Field(..., min_length=3, max_length=50, description="用户ID")
    password: str = Field(..., min_length=6, description="密码")


class UserLogin(BaseModel):
    """用户登录的请求模型。"""
    
    user_id: str = Field(..., description="用户ID")
    password: str = Field(..., description="密码")


class Token(BaseModel):
    """访问令牌响应模型。"""
    
    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")


class TokenData(BaseModel):
    """令牌数据模型。"""
    
    user_id: str | None = Field(None, description="用户ID")
