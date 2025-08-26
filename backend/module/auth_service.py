"""
认证服务模块

本模块提供基于JWT的认证服务，包括：
- 用户认证和授权
- JWT令牌的生成和验证
- 密码加密和验证
- 权限控制和管理员验证
"""

from datetime import datetime, timedelta
import os
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from .models import User, Role
from .database import get_db

# 导入日志配置
from logger_config import get_logger

# 初始化日志记录器
logger = get_logger("auth_service")

# ====================
# 常量定义
# ====================

# OAuth2密码模式配置
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/auth/login")

# 密码加密上下文配置
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ====================
# 安全配置管理
# ====================

def get_security_config() -> Dict[str, Any]:
    """
    动态获取安全配置（完全依赖数据库）
    
    Returns:
        Dict[str, Any]: 包含 SECRET_KEY、ALGORITHM 和 ACCESS_TOKEN_EXPIRE_MINUTES 的安全配置
    
    Raises:
        Exception: 当数据库不可用时，使用临时生成的安全配置
    """
    try:
        from .config_manager import get_security_config as _get_security_config
        config = _get_security_config()
        logger.debug("成功从数据库获取安全配置")
        return config
    except Exception as e:
        logger.error(f"获取动态配置失败: {e}")
        # 数据库不可用时的最后手段：使用临时生成的安全配置
        from .config_manager import generate_secret_key
        
        logger.critical("数据库不可用，使用临时生成的安全配置（仅供紧急使用）")
        
        return {
            'SECRET_KEY': generate_secret_key(),
            'ALGORITHM': 'HS256',
            'ACCESS_TOKEN_EXPIRE_MINUTES': 30
        }

# ====================
# 密码管理功能
# ====================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码是否正确
    
    Args:
        plain_password (str): 明文密码
        hashed_password (str): 已加密的密码哈希
    
    Returns:
        bool: 密码是否匹配
    """
    try:
        result = pwd_context.verify(plain_password, hashed_password)
        logger.debug(f"密码验证结果: {result}")
        return result
    except Exception as e:
        logger.error(f"密码验证失败: {e}")
        return False

def get_password_hash(password: str) -> str:
    """
    生成密码哈希值
    
    Args:
        password (str): 明文密码
    
    Returns:
        str: 加密后的密码哈希
    
    Raises:
        Exception: 当密码加密失败时
    """
    try:
        hashed = pwd_context.hash(password)
        logger.debug("密码哈希生成成功")
        return hashed
    except Exception as e:
        logger.error(f"密码加密失败: {e}")
        raise Exception("密码加密失败")

def get_user(db: Session, username: str) -> Optional[User]:
    """
    根据用户名获取活跃用户（排除已删除用户）
    
    Args:
        db (Session): 数据库会话
        username (str): 用户名
    
    Returns:
        Optional[User]: 用户对象，如果不存在则返回 None
    """
    try:
        user = db.query(User).filter(
            User.username == username,
            User.is_delete == False
        ).first()
        
        if user:
            logger.debug(f"找到用户: {username}, ID: {user.id}")
        else:
            logger.debug(f"用户不存在或已被删除: {username}")
        
        return user
    except Exception as e:
        logger.error(f"查询用户失败: {username}, 错误: {e}")
        return None

def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """
    用户认证
    
    Args:
        db (Session): 数据库会话
        username (str): 用户名
        password (str): 明文密码
    
    Returns:
        Optional[User]: 认证成功返回用户对象，否则返回 None
    """
    logger.debug(f"尝试认证用户: {username}")
    
    # 获取用户
    user = get_user(db, username)
    if not user:
        logger.warning(f"用户不存在: {username}")
        return None
    
    # 验证密码
    if not verify_password(password, user.hashed_password):
        logger.warning(f"密码验证失败: {username}")
        return None
    
    logger.info(f"用户认证成功: {username}, 角色: {user.role}")
    return user

# ====================
# JWT令牌管理
# ====================

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    创建访问令牌
    
    Args:
        data (Dict[str, Any]): 令牌载荷数据
        expires_delta (Optional[timedelta]): 自定义过期时间
    
    Returns:
        str: JWT令牌字符串
    
    Raises:
        Exception: 当令牌创建失败时
    """
    username = data.get("sub", "unknown")
    logger.debug(f"为用户创建访问令牌: {username}")
    
    try:
        # 动态获取安全配置
        security_config = get_security_config()
        SECRET_KEY = security_config['SECRET_KEY']
        ALGORITHM = security_config['ALGORITHM']
        ACCESS_TOKEN_EXPIRE_MINUTES = security_config['ACCESS_TOKEN_EXPIRE_MINUTES']
        
        # 设置过期时间
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        
        # 生成JWT令牌
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        logger.info(f"访问令牌创建成功: {username}")
        return encoded_jwt
        
    except Exception as e:
        logger.error(f"令牌创建失败: {username}, 错误: {e}")
        raise Exception(f"令牌创建失败: {e}")

# ====================
# 权限管理功能
# ====================

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """
    获取当前用户（FastAPI依赖项）
    
    Args:
        token (str): JWT令牌
        db (Session): 数据库会话
    
    Returns:
        User: 当前用户对象
    
    Raises:
        HTTPException: 当令牌无效或用户不存在时
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    logger.debug("尝试验证用户令牌")
    
    try:
        # 动态获取安全配置
        security_config = get_security_config()
        SECRET_KEY = security_config['SECRET_KEY']
        ALGORITHM = security_config['ALGORITHM']
        
        # 解码JWT令牌
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        
        if username is None:
            logger.warning("令牌中未找到用户名")
            raise credentials_exception
            
        logger.debug(f"从令牌中提取用户名: {username}")
        
    except JWTError as e:
        logger.error(f"令牌解码失败: {str(e)}")
        raise credentials_exception
    except Exception as e:
        logger.error(f"令牌验证失败: {str(e)}")
        raise credentials_exception
    
    # 获取用户信息
    user = get_user(db, username=username)
    if user is None:
        logger.warning(f"用户不存在: {username}")
        raise credentials_exception
        
    logger.info(f"用户验证成功: {user.username}, 角色: {user.role}")
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    获取当前活跃用户（FastAPI依赖项）
    
    目前的实现中，所有用户都被认为是活跃的。
    在未来可以扩展为检查用户是否被禁用等。
    
    Args:
        current_user (User): 当前用户
    
    Returns:
        User: 当前活跃用户
    """
    logger.debug(f"检查用户活跃状态: {current_user.username}")
    # 目前所有用户都被认为是活跃的
    # 在未来可以添加更多验证逻辑，例如检查 is_active 字段
    return current_user

async def is_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """
    检查是否为管理员（FastAPI依赖项）
    
    Args:
        current_user (User): 当前用户
    
    Returns:
        User: 管理员用户对象
    
    Raises:
        HTTPException: 当用户不是管理员时
    """
    logger.debug(f"检查用户管理员权限: {current_user.username}, 当前角色: {current_user.role}")
    
    if current_user.role != Role.admin:
        logger.warning(f"用户权限不足: {current_user.username}, 角色: {current_user.role}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="权限不足，需要管理员权限"
        )
    
    logger.info(f"管理员权限验证成功: {current_user.username}")
    return current_user
