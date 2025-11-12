"""用户数据访问仓储。"""

from datetime import datetime
from typing import Optional
from passlib.context import CryptContext

from ...models.user import User
from ...schemas.user import UserCreate
from ..database import get_database

# 密码加密上下文
pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码。"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """获取密码哈希值。"""
    return pwd_context.hash(password)


class UserRepository:
    """用户数据访问仓储。"""
    
    def __init__(self):
        """初始化用户仓储。"""
        self.db = get_database()
    
    def create(self, user_data: UserCreate) -> User:
        """创建新用户。"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # 检查用户是否已存在
            cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_data.user_id,))
            if cursor.fetchone():
                raise ValueError("用户ID已存在")
            
            # 创建用户
            hashed_password = get_password_hash(user_data.password)
            created_at = datetime.utcnow().isoformat()
            
            cursor.execute(
                """INSERT INTO users (user_id, hashed_password, created_at, is_active)
                   VALUES (?, ?, ?, ?)""",
                (user_data.user_id, hashed_password, created_at, 1)
            )
            
            return User(
                user_id=user_data.user_id,
                hashed_password=hashed_password,
                created_at=datetime.fromisoformat(created_at),
                is_active=True
            )
    
    def get_by_id(self, user_id: str) -> Optional[User]:
        """根据用户ID获取用户。"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT user_id, hashed_password, created_at, is_active FROM users WHERE user_id = ?",
                (user_id,)
            )
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return User(
                user_id=row["user_id"],
                hashed_password=row["hashed_password"],
                created_at=datetime.fromisoformat(row["created_at"]),
                is_active=bool(row["is_active"])
            )
    
    def authenticate(self, user_id: str, password: str) -> Optional[User]:
        """验证用户身份。"""
        user = self.get_by_id(user_id)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
