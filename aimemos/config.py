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
    enable_registration: bool = True  # 是否允许注册新用户
    
    # 数据库配置
    # 相对路径是相对于应用启动时的当前工作目录
    database_url: str = "sqlite:///./aimemos.db"
    
    # 文件存储配置
    # 知识库文件存储根目录
    storage_root: str = "./storage"

    # 可选的 OpenAI / LLM 配置（来自 .env 的 OPENAI_BASE_URL / OPENAI_API_KEY）
    # 如果你的环境中没有这些值，保持为 None 即可。
    openai_base_url: str | None = None
    openai_api_key: str | None = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """获取缓存的配置实例。"""
    return Settings()
