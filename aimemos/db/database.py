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
        
        # 初始化数据库
        self._init_database()
    
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
    
    def _init_database(self):
        """初始化数据库表结构和索引。"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 创建用户表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    hashed_password TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    is_active INTEGER NOT NULL DEFAULT 1
                )
            """)
            
            # 创建备忘录表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memos (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    tags TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)
            
            # 创建索引以提高查询性能
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_memos_user_id 
                ON memos (user_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_memos_created_at 
                ON memos (created_at DESC)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_memos_user_created 
                ON memos (user_id, created_at DESC)
            """)
            
            conn.commit()


# 全局数据库实例
_database: Optional[Database] = None


def get_database() -> Database:
    """获取全局数据库实例。"""
    global _database
    if _database is None:
        _database = Database()
    return _database


def init_database():
    """初始化数据库（在应用启动时调用）。"""
    get_database()
