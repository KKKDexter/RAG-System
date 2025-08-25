from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from module.database import get_db
from module.models import User
from module.schemas import UserOut, UserCreate, UserUpdate
from module.auth import get_current_active_user, is_admin

# 导入日志配置
from logger_config import get_logger
logger = get_logger("users_router")

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 创建路由
router = APIRouter(
    prefix="/v1/users",
    tags=["用户"],
)

# 获取当前用户信息
@router.get("/me", response_model=UserOut)
def read_users_me(current_user: User = Depends(get_current_active_user)):
    logger.info(f"用户 {current_user.id} 请求获取自己的信息")
    logger.debug(f"用户信息: 用户名={current_user.username}, 角色={current_user.role}")
    return current_user

# 管理路由
admin_router = APIRouter(
    prefix="/v1/admin",
    tags=["管理"],
)

# 获取所有用户（管理员权限）
@admin_router.get("/users", response_model=List[UserOut])
def get_all_users(
    include_deleted: bool = Query(False, description="是否包含已删除用户"),
    current_user: User = Depends(is_admin),
    db: Session = Depends(get_db)
):
    logger.info(f"管理员 {current_user.id} 请求获取所有用户列表")
    try:
        query = db.query(User)
        if not include_deleted:
            query = query.filter(User.is_delete == False)
        users = query.all()
        logger.info(f"管理员 {current_user.id} 成功获取所有用户列表，共 {len(users)} 个用户")
        logger.debug(f"用户列表: {[user.username for user in users]}")
        return users
    except Exception as e:
        logger.error(f"管理员获取所有用户列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取用户列表失败: {str(e)}")

# 创建用户（管理员权限）
@admin_router.post("/users", response_model=UserOut)
def create_user(
    user_data: UserCreate,
    current_user: User = Depends(is_admin),
    db: Session = Depends(get_db)
):
    logger.info(f"管理员 {current_user.id} 请求创建用户: {user_data.username}")
    
    # 检查用户名是否已存在
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        logger.warning(f"用户名 {user_data.username} 已存在")
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    # 检查邮箱是否已存在
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        logger.warning(f"邮箱 {user_data.email} 已存在")
        raise HTTPException(status_code=400, detail="邮箱已存在")
    
    try:
        # 加密密码
        hashed_password = pwd_context.hash(user_data.password)
        
        # 创建用户
        db_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            phone=user_data.phone,
            role=user_data.role
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        logger.info(f"管理员 {current_user.id} 成功创建用户: {db_user.username}, ID: {db_user.id}")
        return db_user
    except Exception as e:
        logger.error(f"创建用户失败: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建用户失败: {str(e)}")

# 获取单个用户（管理员权限）
@admin_router.get("/users/{user_id}", response_model=UserOut)
def get_user(
    user_id: int,
    current_user: User = Depends(is_admin),
    db: Session = Depends(get_db)
):
    logger.info(f"管理员 {current_user.id} 请求获取用户 {user_id} 的信息")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logger.warning(f"用户 {user_id} 不存在")
        raise HTTPException(status_code=404, detail="用户不存在")
    
    logger.info(f"管理员 {current_user.id} 成功获取用户 {user_id} 的信息")
    return user

# 更新用户（管理员权限）
@admin_router.put("/users/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(is_admin),
    db: Session = Depends(get_db)
):
    logger.info(f"管理员 {current_user.id} 请求更新用户 {user_id} 的信息")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logger.warning(f"用户 {user_id} 不存在")
        raise HTTPException(status_code=404, detail="用户不存在")
    
    try:
        # 更新字段
        update_data = user_data.model_dump(exclude_unset=True)
        
        # 如果更新密码，需要加密
        if "password" in update_data:
            update_data["hashed_password"] = pwd_context.hash(update_data.pop("password"))
        
        # 检查用户名是否重复
        if "username" in update_data and update_data["username"] != user.username:
            existing_user = db.query(User).filter(User.username == update_data["username"]).first()
            if existing_user:
                raise HTTPException(status_code=400, detail="用户名已存在")
        
        # 检查邮箱是否重复
        if "email" in update_data and update_data["email"] != user.email:
            existing_email = db.query(User).filter(User.email == update_data["email"]).first()
            if existing_email:
                raise HTTPException(status_code=400, detail="邮箱已存在")
        
        # 应用更新
        for field, value in update_data.items():
            setattr(user, field, value)
        
        db.commit()
        db.refresh(user)
        
        logger.info(f"管理员 {current_user.id} 成功更新用户 {user_id} 的信息")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新用户失败: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新用户失败: {str(e)}")

# 逻辑删除用户（管理员权限）
@admin_router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    current_user: User = Depends(is_admin),
    db: Session = Depends(get_db)
):
    logger.info(f"管理员 {current_user.id} 请求删除用户 {user_id}")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logger.warning(f"用户 {user_id} 不存在")
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 不能删除自己
    if user.id == current_user.id:
        logger.warning(f"管理员 {current_user.id} 尝试删除自己")
        raise HTTPException(status_code=400, detail="不能删除自己")
    
    try:
        # 逻辑删除
        user.is_delete = True
        db.commit()
        
        logger.info(f"管理员 {current_user.id} 成功删除用户 {user_id}")
        return {"message": "用户已成功删除"}
    except Exception as e:
        logger.error(f"删除用户失败: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除用户失败: {str(e)}")

# 恢复用户（管理员权限）
@admin_router.post("/users/{user_id}/restore")
def restore_user(
    user_id: int,
    current_user: User = Depends(is_admin),
    db: Session = Depends(get_db)
):
    logger.info(f"管理员 {current_user.id} 请求恢复用户 {user_id}")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logger.warning(f"用户 {user_id} 不存在")
        raise HTTPException(status_code=404, detail="用户不存在")
    
    try:
        # 恢复用户
        user.is_delete = False
        db.commit()
        
        logger.info(f"管理员 {current_user.id} 成功恢复用户 {user_id}")
        return {"message": "用户已成功恢复"}
    except Exception as e:
        logger.error(f"恢复用户失败: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"恢复用户失败: {str(e)}")

# 获取系统设置（管理员权限）
@admin_router.get("/settings")
def get_system_settings(
    current_user: User = Depends(is_admin)
):
    logger.info(f"管理员 {current_user.id} 请求获取系统设置")
    
    try:
        # 导入配置信息
        import os
        env = os.environ.get('ENVIRONMENT', 'dev')
        if env == 'prod':
            from config.prod import (
                EMBEDDING_MODEL_API_KEY, EMBEDDING_MODEL_NAME,
                CHAT_MODEL_API_KEY, CHAT_MODEL_NAME, CHAT_MODEL_URL,
                MILVUS_HOST, MILVUS_PORT, MILVUS_USERNAME, MILVUS_PASSWORD,
                REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, REDIS_DB,
                VECTOR_DIM
            )
        else:
            from config.dev import (
                EMBEDDING_MODEL_API_KEY, EMBEDDING_MODEL_NAME,
                CHAT_MODEL_API_KEY, CHAT_MODEL_NAME, CHAT_MODEL_URL,
                MILVUS_HOST, MILVUS_PORT, MILVUS_USERNAME, MILVUS_PASSWORD,
                REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, REDIS_DB,
                VECTOR_DIM
            )
        
        # 构建设置响应
        settings = {
            "llm": {
                "defaultModel": CHAT_MODEL_NAME,
                "apiKey": CHAT_MODEL_API_KEY if CHAT_MODEL_API_KEY != "None" else "",
                "baseUrl": CHAT_MODEL_URL,
                "temperature": 0.7,
                "maxTokens": 4000,
                "embeddingModel": EMBEDDING_MODEL_NAME,
                "embeddingApiKey": EMBEDDING_MODEL_API_KEY if EMBEDDING_MODEL_API_KEY != "None" else ""
            },
            "milvus": {
                "host": MILVUS_HOST,
                "port": MILVUS_PORT,
                "username": MILVUS_USERNAME or "",
                "password": MILVUS_PASSWORD or "",
                "vectorDim": VECTOR_DIM,
                "indexType": "IVF_FLAT",
                "metricType": "L2"
            },
            "redis": {
                "host": REDIS_HOST,
                "port": REDIS_PORT,
                "password": REDIS_PASSWORD or "",
                "database": REDIS_DB,
                "ttl": 3600
            },
            "system": {
                "chunkSize": 1000,
                "chunkOverlap": 200,
                "concurrency": 4,
                "maxDocumentSize": 20,
                "debugMode": False
            }
        }
        
        logger.info(f"管理员 {current_user.id} 成功获取系统设置")
        return settings
    except Exception as e:
        logger.error(f"获取系统设置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取系统设置失败: {str(e)}")

# 保存系统设置（管理员权限）
@admin_router.post("/settings")
def save_system_settings(
    settings_data: dict,
    current_user: User = Depends(is_admin)
):
    logger.info(f"管理员 {current_user.id} 请求保存系统设置")
    
    try:
        # 这里可以实现设置的持久化保存
        # 目前返回成功消息，实际项目中可以保存到数据库或配置文件
        logger.info(f"系统设置保存请求: {settings_data}")
        
        # 注意：在实际项目中，这里应该:
        # 1. 验证设置数据的有效性
        # 2. 将设置保存到数据库或配置文件
        # 3. 可能需要重启某些服务以应用新设置
        
        logger.info(f"管理员 {current_user.id} 成功保存系统设置")
        return {"message": "系统设置保存成功，部分设置需要重启服务才能生效"}
    except Exception as e:
        logger.error(f"保存系统设置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"保存系统设置失败: {str(e)}")

# 获取系统日志（管理员权限）
@admin_router.get("/logs")
def get_system_logs(
    limit: int = Query(100, description="返回日志条数"),
    level: str = Query(None, description="日志级别过滤"),
    current_user: User = Depends(is_admin)
):
    logger.info(f"管理员 {current_user.id} 请求获取系统日志")
    
    try:
        # 这里可以实现日志查询功能
        # 目前返回模拟数据，实际项目中应该从日志文件或数据库中读取
        logs = [
            {
                "timestamp": "2024-01-01 12:00:00",
                "level": "INFO",
                "message": "系统启动成功",
                "source": "main"
            },
            {
                "timestamp": "2024-01-01 12:01:00",
                "level": "INFO",
                "message": "用户登录成功",
                "source": "auth"
            }
        ]
        
        logger.info(f"管理员 {current_user.id} 成功获取系统日志，共 {len(logs)} 条")
        return logs
    except Exception as e:
        logger.error(f"获取系统日志失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取系统日志失败: {str(e)}")
