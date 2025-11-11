"""Main entry point for AI Memos."""

import uvicorn
from .config import get_settings


def main():
    """Run the application."""
    settings = get_settings()
    
    uvicorn.run(
        "aimemos.app:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )


if __name__ == "__main__":
    main()
