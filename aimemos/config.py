"""AI Memos 的配置管理。"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置。"""
    
    app_name: str = "AI Memos"
    app_version: str = "0.1.0"
    debug: bool = False
    
    # 服务器配置
    host: str = "0.0.0.0"
    port: int = 8000
    
    # API 配置
    api_prefix: str = "/api/v1"
    
    # 认证配置
    secret_key: str = "your-secret-key-change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # 用户注册配置
    enable_auto_registration: bool = True  # 是否开启自动注册功能
    
    # 数据库配置
    # 相对路径是相对于应用启动时的当前工作目录
    database_url: str = "sqlite:///./aimemos.db"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """获取缓存的配置实例。"""
    return Settings()
