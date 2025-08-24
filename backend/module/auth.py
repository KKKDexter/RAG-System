from datetime import datetime, timedelta
import os
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

# 根据环境变量动态导入配置
env = os.environ.get('ENVIRONMENT', 'dev')
if env == 'prod':
    from config.prod import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
else:
    from config.dev import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

from .models import User, Role
from .database import get_db

# 导入日志配置
from logger_config import get_logger
logger = get_logger("auth")

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2密码模式
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# 密码验证函数
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# 生成密码哈希
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# 根据用户名获取用户
def get_user(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()

# 用户认证
def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    logger.debug(f"尝试认证用户: {username}")
    user = get_user(db, username)
    if not user:
        logger.warning(f"用户不存在: {username}")
        return None
    if not verify_password(password, user.hashed_password):
        logger.warning(f"密码验证失败: {username}")
        return None
    logger.info(f"用户认证成功: {username}")
    return user

# 创建访问令牌
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    username = data.get("sub", "unknown")
    logger.debug(f"为用户创建访问令牌: {username}")
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    logger.info(f"访问令牌创建成功: {username}")
    return encoded_jwt

# 获取当前用户（依赖项）
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    logger.debug("尝试验证用户令牌")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            logger.warning("令牌中未找到用户名")
            raise credentials_exception
        token_data = {"username": username}
        logger.debug(f"从令牌中提取用户名: {username}")
    except JWTError as e:
        logger.error(f"令牌解码失败: {str(e)}")
        raise credentials_exception
    user = get_user(db, username=token_data["username"])
    if user is None:
        logger.warning(f"用户不存在: {token_data['username']}")
        raise credentials_exception
    logger.info(f"用户验证成功: {user.username}, 角色: {user.role}")
    return user

# 获取当前活跃用户（依赖项）
async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    return current_user

# 检查是否为管理员（依赖项）
async def is_admin(current_user: User = Depends(get_current_active_user)) -> User:
    logger.debug(f"检查用户管理员权限: {current_user.username}, 当前角色: {current_user.role}")
    if current_user.role != Role.admin:
        logger.warning(f"用户权限不足: {current_user.username}, 角色: {current_user.role}")
        raise HTTPException(status_code=403, detail="权限不足")
    logger.info(f"管理员权限验证成功: {current_user.username}")
    return current_user