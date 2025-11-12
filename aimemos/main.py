"""AI Memos 的主入口点。"""

import uvicorn
from .config import get_settings


def main():
    """运行应用。"""
    settings = get_settings()
    
    uvicorn.run(
        "aimemos.app:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )


if __name__ == "__main__":
    main()
