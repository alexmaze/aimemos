"""用户数据访问仓储。"""

from datetime import datetime
from typing import Optional
from passlib.context import CryptContext

from ...models.user import User
from ...schemas.user import UserCreate

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
        self._users: dict[str, User] = {}
    
    def create(self, user_data: UserCreate) -> User:
        """创建新用户。"""
        if user_data.user_id in self._users:
            raise ValueError("用户ID已存在")
        
        hashed_password = get_password_hash(user_data.password)
        user = User(
            user_id=user_data.user_id,
            hashed_password=hashed_password,
            created_at=datetime.utcnow(),
            is_active=True
        )
        
        self._users[user_data.user_id] = user
        return user
    
    def get_by_id(self, user_id: str) -> Optional[User]:
        """根据用户ID获取用户。"""
        return self._users.get(user_id)
    
    def authenticate(self, user_id: str, password: str) -> Optional[User]:
        """验证用户身份。"""
        user = self.get_by_id(user_id)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
