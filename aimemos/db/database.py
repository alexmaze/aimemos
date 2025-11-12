"""数据库管理和初始化。"""

import sqlite3
from pathlib import Path
from typing import Optional
from contextlib import contextmanager

from ..config import get_settings


class Database:
    """SQLite 数据库管理器。"""
    
    def __init__(self, database_url: Optional[str] = None):
        """初始化数据库连接。
        
        Args:
            database_url: 数据库 URL，格式为 sqlite:///path/to/db.db
        """
        if database_url is None:
            settings = get_settings()
            database_url = settings.database_url
        
        # 从 URL 提取文件路径
        if database_url.startswith("sqlite:///"):
            self.db_path = database_url.replace("sqlite:///", "")
        else:
            raise ValueError(f"不支持的数据库 URL: {database_url}")
        
        # 确保数据库目录存在
        db_file = Path(self.db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接上下文管理器。"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 允许通过列名访问
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


# 全局数据库实例
_database: Optional[Database] = None


def get_database() -> Database:
    """获取全局数据库实例。"""
    global _database
    if _database is None:
        _database = Database()
    return _database


def init_database():
    """初始化数据库（在应用启动时调用）。
    
    注意：具体的表初始化由各个 Repository 类负责。
    """
    # 仅创建数据库实例，表初始化由各仓储类完成
    get_database()
