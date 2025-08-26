"""
系统配置管理 API
提供系统配置的增删改查功能
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from module.database import get_db
from module.models import User, SystemConfig, ConfigType
from module.schemas import SystemConfigCreate, SystemConfigUpdate, SystemConfigOut
from module.auth_service import get_current_active_user
from module.config_manager import config_manager

router = APIRouter(prefix="/v1/config", tags=["系统配置"])

def check_admin_permission(current_user: User = Depends(get_current_active_user)):
    """检查管理员权限"""
    if current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以管理系统配置"
        )
    return current_user

@router.get("/", response_model=List[SystemConfigOut])
async def get_all_configs(
    include_sensitive: bool = False,
    current_user: User = Depends(check_admin_permission),
    db: Session = Depends(get_db)
):
    """
    获取所有系统配置
    - include_sensitive: 是否包含敏感信息（默认为 False）
    """
    try:
        if include_sensitive:
            # 获取所有配置（包括敏感信息）
            configs = db.query(SystemConfig).filter(
                SystemConfig.is_active == True
            ).all()
        else:
            # 只获取非敏感配置
            configs = db.query(SystemConfig).filter(
                SystemConfig.is_active == True,
                SystemConfig.is_sensitive == False
            ).all()
        
        result = []
        for config in configs:
            config_dict = {
                "id": config.id,
                "config_key": config.config_key,
                "config_value": config.config_value if not config.is_sensitive or include_sensitive else "***",
                "config_type": config.config_type,
                "description": config.description,
                "is_sensitive": config.is_sensitive,
                "is_active": config.is_active,
                "created_at": config.created_at,
                "updated_at": config.updated_at
            }
            result.append(SystemConfigOut(**config_dict))
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取配置失败: {str(e)}"
        )

@router.get("/{config_key}", response_model=SystemConfigOut)
async def get_config(
    config_key: str,
    current_user: User = Depends(check_admin_permission),
    db: Session = Depends(get_db)
):
    """获取指定的系统配置"""
    config = db.query(SystemConfig).filter(
        SystemConfig.config_key == config_key,
        SystemConfig.is_active == True
    ).first()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"配置项 {config_key} 不存在"
        )
    
    # 如果是敏感信息，隐藏具体值
    config_dict = {
        "id": config.id,
        "config_key": config.config_key,
        "config_value": config.config_value if not config.is_sensitive else "***",
        "config_type": config.config_type,
        "description": config.description,
        "is_sensitive": config.is_sensitive,
        "is_active": config.is_active,
        "created_at": config.created_at,
        "updated_at": config.updated_at
    }
    
    return SystemConfigOut(**config_dict)

@router.post("/", response_model=SystemConfigOut)
async def create_config(
    config_data: SystemConfigCreate,
    current_user: User = Depends(check_admin_permission),
    db: Session = Depends(get_db)
):
    """创建新的系统配置"""
    # 检查配置键是否已存在
    existing_config = db.query(SystemConfig).filter(
        SystemConfig.config_key == config_data.config_key
    ).first()
    
    if existing_config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"配置项 {config_data.config_key} 已存在"
        )
    
    try:
        # 使用配置服务创建配置
        success = config_manager.set_config(
            key=config_data.config_key,
            value=config_data.config_value,
            config_type=config_data.config_type,
            description=config_data.description or "",
            is_sensitive=config_data.is_sensitive,
            db=db
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="创建配置失败"
            )
        
        # 获取新创建的配置
        new_config = db.query(SystemConfig).filter(
            SystemConfig.config_key == config_data.config_key
        ).first()
        
        config_dict = {
            "id": new_config.id,
            "config_key": new_config.config_key,
            "config_value": new_config.config_value if not new_config.is_sensitive else "***",
            "config_type": new_config.config_type,
            "description": new_config.description,
            "is_sensitive": new_config.is_sensitive,
            "is_active": new_config.is_active,
            "created_at": new_config.created_at,
            "updated_at": new_config.updated_at
        }
        
        return SystemConfigOut(**config_dict)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建配置失败: {str(e)}"
        )

@router.put("/{config_key}", response_model=SystemConfigOut)
async def update_config(
    config_key: str,
    config_data: SystemConfigUpdate,
    current_user: User = Depends(check_admin_permission),
    db: Session = Depends(get_db)
):
    """更新系统配置"""
    # 检查配置是否存在
    config = db.query(SystemConfig).filter(
        SystemConfig.config_key == config_key
    ).first()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"配置项 {config_key} 不存在"
        )
    
    try:
        # 更新配置字段
        if config_data.config_value is not None:
            config.config_value = config_data.config_value
        if config_data.config_type is not None:
            config.config_type = config_data.config_type
        if config_data.description is not None:
            config.description = config_data.description
        if config_data.is_sensitive is not None:
            config.is_sensitive = config_data.is_sensitive
        if config_data.is_active is not None:
            config.is_active = config_data.is_active
        
        db.commit()
        db.refresh(config)
        
        # 更新缓存
        if config.is_active and config_data.config_value is not None:
            # 使用配置管理器的公有方法更新缓存
            converted_value = config_manager.convert_config_value(
                config.config_value, config.config_type
            )
            config_manager.update_config_cache({config_key: converted_value})
        elif not config.is_active:
            # 如果配置被禁用，需要从缓存中移除（通过重新加载实现）
            config_manager.clear_cache()
            config_manager._load_config_from_db(db)
        
        config_dict = {
            "id": config.id,
            "config_key": config.config_key,
            "config_value": config.config_value if not config.is_sensitive else "***",
            "config_type": config.config_type,
            "description": config.description,
            "is_sensitive": config.is_sensitive,
            "is_active": config.is_active,
            "created_at": config.created_at,
            "updated_at": config.updated_at
        }
        
        return SystemConfigOut(**config_dict)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新配置失败: {str(e)}"
        )

@router.delete("/{config_key}")
async def delete_config(
    config_key: str,
    current_user: User = Depends(check_admin_permission),
    db: Session = Depends(get_db)
):
    """删除系统配置（软删除，设置为非活跃状态）"""
    success = config_manager.delete_config(config_key, db)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"配置项 {config_key} 不存在或删除失败"
        )
    
    return {"message": f"配置项 {config_key} 已删除"}

@router.post("/refresh-cache")
async def refresh_cache(
    current_user: User = Depends(check_admin_permission),
    db: Session = Depends(get_db)
):
    """刷新配置缓存"""
    try:
        config_manager.clear_cache()
        # 使用公有方法获取缓存信息
        cache_info = config_manager.get_cache_info()
        
        # 重新加载配置
        config_manager.get_config("dummy_key", None, db)  # 触发加载
        
        updated_cache_info = config_manager.get_cache_info()
        
        return {
            "message": "配置缓存已刷新",
            "cached_configs": updated_cache_info["cached_configs_count"]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"刷新缓存失败: {str(e)}"
        )

@router.get("/security/info")
async def get_security_config(
    current_user: User = Depends(check_admin_permission),
    db: Session = Depends(get_db)
):
    """获取安全配置信息（隐藏敏感值）"""
    try:
        security_configs = config_manager.get_security_config(db)
        
        # 隐藏敏感信息
        result = {}
        for key, value in security_configs.items():
            if key == 'SECRET_KEY':
                result[key] = "***" if value else None
            else:
                result[key] = value
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取安全配置失败: {str(e)}"
        )