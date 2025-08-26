"""
统一配置管理模块
整合了配置服务和配置加载器的功能，提供完整的配置管理解决方案
"""

import os
import sys
import json
import secrets
import logging
from typing import Any, Dict, Optional, Union
from sqlalchemy.orm import Session
from .models import SystemConfig, ConfigType
from .database import get_db

logger = logging.getLogger(__name__)

def generate_secret_key(length: int = 32) -> str:
    """
    生成安全的随机密钥
    
    Args:
        length: 密钥长度（字节数），默认32字节
    
    Returns:
        十六进制格式的安全密钥字符串
    """
    return secrets.token_hex(length)

class ConfigManager:
    """统一配置管理类，整合配置服务和配置加载功能"""
    
    def __init__(self):
        # 配置缓存
        self._cache: Dict[str, Any] = {}
        self._cache_loaded = False
        
        # 安全配置缓存（原config_loader功能）
        self._security_config_cache: Dict[str, Any] = {}
        self._config_loaded = False
    
    def _convert_value(self, value: str, config_type: ConfigType) -> Any:
        """根据配置类型转换配置值"""
        if config_type == ConfigType.integer:
            return int(value)
        elif config_type == ConfigType.float:
            return float(value)
        elif config_type == ConfigType.boolean:
            return value.lower() in ('true', '1', 'yes', 'on')
        else:  # string
            return value
    
    def _load_config_from_db(self, db: Session) -> None:
        """从数据库加载所有活跃的配置项到缓存"""
        try:
            configs = db.query(SystemConfig).filter(
                SystemConfig.is_active == True
            ).all()
            
            for config in configs:
                try:
                    converted_value = self._convert_value(config.config_value, config.config_type)
                    self._cache[config.config_key] = converted_value
                except (ValueError, TypeError) as e:
                    logger.warning(f"配置项 {config.config_key} 值转换失败: {e}")
                    self._cache[config.config_key] = config.config_value
            
            self._cache_loaded = True
            logger.info(f"从数据库加载了 {len(configs)} 个配置项")
            
        except Exception as e:
            logger.error(f"从数据库加载配置失败: {e}")
            self._cache_loaded = False
    
    def get_config(self, key: str, default: Any = None, db: Optional[Session] = None) -> Any:
        """
        获取配置值，优先从缓存读取，缓存未命中时从数据库读取
        """
        # 如果缓存未加载，尝试加载
        if not self._cache_loaded and db:
            self._load_config_from_db(db)
        
        # 从缓存获取
        if key in self._cache:
            return self._cache[key]
        
        # 如果有数据库连接，尝试从数据库获取单个配置
        if db:
            try:
                config = db.query(SystemConfig).filter(
                    SystemConfig.config_key == key,
                    SystemConfig.is_active == True
                ).first()
                
                if config:
                    converted_value = self._convert_value(config.config_value, config.config_type)
                    self._cache[key] = converted_value
                    return converted_value
            except Exception as e:
                logger.error(f"从数据库获取配置 {key} 失败: {e}")
        
        # 最后返回默认值
        return default
    
    def set_config(self, key: str, value: Any, config_type: ConfigType = ConfigType.string, 
                   description: str = "", is_sensitive: bool = False, db: Session = None) -> bool:
        """
        设置配置值，同时更新数据库和缓存
        """
        if not db:
            logger.error("设置配置需要数据库连接")
            return False
        
        try:
            # 将值转换为字符串存储
            str_value = str(value)
            
            # 查找现有配置
            config = db.query(SystemConfig).filter(
                SystemConfig.config_key == key
            ).first()
            
            if config:
                # 更新现有配置
                config.config_value = str_value
                config.config_type = config_type
                config.description = description
                config.is_sensitive = is_sensitive
                config.is_active = True
            else:
                # 创建新配置
                config = SystemConfig(
                    config_key=key,
                    config_value=str_value,
                    config_type=config_type,
                    description=description,
                    is_sensitive=is_sensitive,
                    is_active=True
                )
                db.add(config)
            
            db.commit()
            
            # 更新缓存
            converted_value = self._convert_value(str_value, config_type)
            self._cache[key] = converted_value
            
            # 如果是安全配置，也更新安全配置缓存
            if key in ['SECRET_KEY', 'ALGORITHM', 'ACCESS_TOKEN_EXPIRE_MINUTES']:
                self._security_config_cache[key] = converted_value
            
            logger.info(f"配置 {key} 已更新")
            return True
            
        except Exception as e:
            logger.error(f"设置配置 {key} 失败: {e}")
            db.rollback()
            return False
    
    def delete_config(self, key: str, db: Session) -> bool:
        """
        删除配置项（软删除，设置为非活跃状态）
        """
        try:
            config = db.query(SystemConfig).filter(
                SystemConfig.config_key == key
            ).first()
            
            if config:
                config.is_active = False
                db.commit()
                
                # 从缓存移除
                if key in self._cache:
                    del self._cache[key]
                
                # 从安全配置缓存移除
                if key in self._security_config_cache:
                    del self._security_config_cache[key]
                
                logger.info(f"配置 {key} 已删除")
                return True
            else:
                logger.warning(f"配置 {key} 不存在")
                return False
                
        except Exception as e:
            logger.error(f"删除配置 {key} 失败: {e}")
            db.rollback()
            return False
    
    def get_all_configs(self, include_sensitive: bool = False, db: Session = None) -> Dict[str, Any]:
        """
        获取所有配置项
        """
        if not self._cache_loaded and db:
            self._load_config_from_db(db)
        
        if include_sensitive:
            return self._cache.copy()
        
        # 如果不包含敏感信息，需要从数据库过滤
        if db:
            try:
                configs = db.query(SystemConfig).filter(
                    SystemConfig.is_active == True,
                    SystemConfig.is_sensitive == False
                ).all()
                
                result = {}
                for config in configs:
                    if config.config_key in self._cache:
                        result[config.config_key] = self._cache[config.config_key]
                
                return result
            except Exception as e:
                logger.error(f"获取非敏感配置失败: {e}")
        
        return {}
    
    def load_security_config_from_db(self) -> Dict[str, Any]:
        """从数据库加载安全配置"""
        if self._config_loaded and self._security_config_cache:
            return self._security_config_cache
        
        try:
            db = next(get_db())
            try:
                security_config = self.get_security_config(db)
                self._security_config_cache = security_config
                self._config_loaded = True
                logger.info("成功从数据库加载安全配置")
                return security_config
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"从数据库加载安全配置失败: {e}")
            logger.warning("数据库不可用，使用临时生成的安全配置")
            
            # 仅在数据库完全不可用时使用临时配置
            fallback_config = {
                'SECRET_KEY': generate_secret_key(),  # 临时生成安全密钥
                'ALGORITHM': 'HS256',  # 固定算法
                'ACCESS_TOKEN_EXPIRE_MINUTES': 30  # 默认过期时间
            }
            
            logger.warning(f"使用临时安全配置： SECRET_KEY=<已生成>, ALGORITHM={fallback_config['ALGORITHM']}, ACCESS_TOKEN_EXPIRE_MINUTES={fallback_config['ACCESS_TOKEN_EXPIRE_MINUTES']}")
            
            self._security_config_cache = fallback_config
            return fallback_config
    
    def get_security_config(self, db: Session = None) -> Dict[str, Any]:
        """
        获取安全相关配置，优先从数据库读取，如果不存在则使用环境变量或默认值
        """
        if not db:
            # 如果没有提供db连接，从缓存获取或重新加载
            return self.load_security_config_from_db()
        
        security_configs = {
            'SECRET_KEY': self.get_config('SECRET_KEY', os.getenv("SECRET_KEY", "02lkAtLdaHZbln18tm37mAGdgo90wke8"), db),
            'ALGORITHM': self.get_config('ALGORITHM', os.getenv("ALGORITHM", "HS256"), db),
            'ACCESS_TOKEN_EXPIRE_MINUTES': self.get_config('ACCESS_TOKEN_EXPIRE_MINUTES', 
                                                         int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")), db)
        }
        return security_configs
    
    def update_config_cache(self, config: Dict[str, Any]):
        """更新配置缓存（当配置变更时调用）"""
        self._cache.update(config)
        self._security_config_cache.update(config)
        logger.info("配置缓存已更新")
    
    def clear_cache(self):
        """清空配置缓存"""
        self._cache.clear()
        self._cache_loaded = False
        self._security_config_cache.clear()
        self._config_loaded = False
        logger.info("配置缓存已清空")
    
    def convert_config_value(self, value: str, config_type: ConfigType) -> Any:
        """
        公有方法：根据配置类型转换配置值
        
        Args:
            value (str): 配置值字符串
            config_type (ConfigType): 配置类型
        
        Returns:
            Any: 转换后的值
        """
        return self._convert_value(value, config_type)
    
    def get_cache_info(self) -> Dict[str, Any]:
        """
        获取缓存信息
        
        Returns:
            Dict[str, Any]: 缓存状态信息
        """
        return {
            "cached_configs_count": len(self._cache),
            "cache_loaded": self._cache_loaded,
            "security_cache_count": len(self._security_config_cache),
            "security_config_loaded": self._config_loaded,
            "non_sensitive_keys": [key for key in self._cache.keys() if not key.startswith('SECRET')]
        }

def update_runtime_config():
    """更新运行时配置（在应用启动后调用）"""
    try:
        # 加载安全配置
        security_config = config_manager.load_security_config_from_db()
        
        # 更新当前模块的配置
        current_module = sys.modules[__name__]
        for key, value in security_config.items():
            setattr(current_module, key, value)
        
        # 同时更新config模块
        env = os.environ.get('ENVIRONMENT', 'dev')
        if env == 'prod':
            config_module_name = 'config.prod'
        else:
            config_module_name = 'config.dev'
        
        if config_module_name in sys.modules:
            config_module = sys.modules[config_module_name]
            for key, value in security_config.items():
                setattr(config_module, key, value)
            logger.info(f"已更新 {config_module_name} 模块的安全配置")
        
        logger.info("运行时配置更新完成")
        return True
        
    except Exception as e:
        logger.error(f"更新运行时配置失败: {e}")
        return False

# 全局配置管理器实例
config_manager = ConfigManager()

# 便捷函数
def get_config(key: str, default: Any = None) -> Any:
    """获取配置值的便捷函数"""
    db = next(get_db())
    try:
        return config_manager.get_config(key, default, db)
    finally:
        db.close()

def set_config(key: str, value: Any, config_type: ConfigType = ConfigType.string, 
               description: str = "", is_sensitive: bool = False) -> bool:
    """设置配置值的便捷函数"""
    db = next(get_db())
    try:
        return config_manager.set_config(key, value, config_type, description, is_sensitive, db)
    finally:
        db.close()

def get_security_config() -> Dict[str, Any]:
    """获取安全配置的便捷函数"""
    return config_manager.get_security_config()

# 初始化时的默认配置（避免导入错误）
# 自动生成安全的 SECRET_KEY
SECRET_KEY = generate_secret_key()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

logger.info(f"初始化默认安全配置，已生成安全密钥（长度: {len(SECRET_KEY)} 字符）")