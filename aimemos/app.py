"""AI Memos 的 FastAPI 应用。"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .routes import router


def create_app() -> FastAPI:
    """创建并配置 FastAPI 应用。"""
    settings = get_settings()
    
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="基于 AI 的个人知识库服务",
        debug=settings.debug,
    )
    
    # 添加 CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 包含路由
    app.include_router(router, prefix=settings.api_prefix, tags=["memos"])
    
    @app.get("/")
    async def root():
        """根端点。"""
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "status": "running"
        }
    
    @app.get("/health")
    async def health():
        """健康检查端点。"""
        return {"status": "healthy"}
    
    return app


app = create_app()
