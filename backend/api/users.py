from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from module.database import get_db
from module.models import User
from module.schemas import UserOut
from module.auth import get_current_active_user, is_admin

# 导入日志配置
from logger_config import get_logger
logger = get_logger("users_router")

# 创建路由
router = APIRouter(
    prefix="/api/v1/users",
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
    prefix="/api/v1/admin",
    tags=["管理"],
)

# 获取所有用户（管理员权限）
@admin_router.get("/users", response_model=List[UserOut])
def get_all_users(
    current_user: User = Depends(is_admin),
    db: Session = Depends(get_db)
):
    logger.info(f"管理员 {current_user.id} 请求获取所有用户列表")
    try:
        users = db.query(User).all()
        logger.info(f"管理员 {current_user.id} 成功获取所有用户列表，共 {len(users)} 个用户")
        logger.debug(f"用户列表: {[user.username for user in users]}")
        return users
    except Exception as e:
        logger.error(f"管理员获取所有用户列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取用户列表失败: {str(e)}")