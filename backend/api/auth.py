from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from module.database import get_db
from module.models import User
from module.schemas import UserOut, UserCreate, Token, LoginRequest
from module.auth import (
    authenticate_user,
    create_access_token,
    get_password_hash,
    get_user
)
from config.dev import ACCESS_TOKEN_EXPIRE_MINUTES
from module.milvus_service import create_user_collection

# 导入日志配置
from logger_config import get_logger
logger = get_logger("auth_router")

# 创建路由
router = APIRouter(
    prefix="/v1/auth",
    tags=["认证"],
)

# 用户注册
@router.post("/signup", response_model=UserOut)
def signup(user: UserCreate, db: Session = Depends(get_db)):
    logger.info(f"收到用户注册请求，用户名: {user.username}")
    
    db_user = get_user(db, username=user.username)
    if db_user:
        logger.warning(f"用户注册失败：用户名 '{user.username}' 已存在")
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    # 检查邮箱是否已被使用
    if db.query(User).filter(User.email == user.email).first():
        logger.warning(f"用户注册失败：邮箱 '{user.email}' 已被使用")
        raise HTTPException(status_code=400, detail="邮箱已被使用")
    
    # 创建新用户
    logger.debug(f"创建新用户：{user.username}，角色：{user.role}")
    try:
        hashed_password = get_password_hash(user.password)
        db_user = User(
            username=user.username,
            email=user.email,
            hashed_password=hashed_password,
            phone=user.phone,
            role=user.role,
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        logger.info(f"用户创建成功，用户ID: {db_user.id}")
        
        # 创建用户的Milvus集合
        logger.debug(f"为用户 {db_user.id} 创建Milvus集合")
        create_user_collection(db_user.id)
        
        logger.info(f"用户注册成功完成：{user.username}")
        return db_user
    except Exception as e:
        logger.error(f"用户注册过程中发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"注册失败：{str(e)}")

# 用户登录
@router.post("/login", response_model=Token)
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    logger.info(f"收到用户登录请求，用户名: {login_data.username}")
    
    try:
        user = authenticate_user(db, login_data.username, login_data.password)
        if not user:
            logger.warning(f"用户登录失败：用户名 '{login_data.username}' 验证失败")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        logger.debug(f"用户 {login_data.username} 验证成功，生成访问令牌")
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username},
            expires_delta=access_token_expires,
        )
        
        logger.info(f"用户登录成功：{login_data.username}，用户ID: {user.id}")
        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException:
        # 已经在authenticate_user中处理了登录失败的日志
        raise
    except Exception as e:
        logger.error(f"用户登录过程中发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"登录失败：{str(e)}")