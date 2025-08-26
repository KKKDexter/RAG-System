"""
通用服务基类

本模块提供通用的CRUD操作基类，减少重复的数据库操作代码

作者: RAG-System Team
版本: 1.0
"""

from typing import Type, TypeVar, Generic, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import Column
from pydantic import BaseModel
from logger_config import get_logger

logger = get_logger("base_service")

# 类型变量
ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

class BaseService(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    通用服务基类
    提供标准的CRUD操作，减少重复代码
    """
    
    def __init__(self, model: Type[ModelType], resource_name: str = "资源"):
        """
        初始化服务
        
        Args:
            model: SQLAlchemy模型类
            resource_name: 资源名称，用于日志记录
        """
        self.model = model
        self.resource_name = resource_name
    
    def create(self, db: Session, *, obj_in: CreateSchemaType, **kwargs) -> ModelType:
        """
        创建资源
        
        Args:
            db: 数据库会话
            obj_in: 创建数据
            **kwargs: 额外的字段值
        
        Returns:
            创建的资源对象
        """
        logger.info(f"创建{self.resource_name}")
        
        # 转换为字典
        obj_data = obj_in.model_dump() if hasattr(obj_in, 'model_dump') else obj_in.dict()
        
        # 添加额外字段
        obj_data.update(kwargs)
        
        # 创建数据库对象
        db_obj = self.model(**obj_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        
        logger.info(f"{self.resource_name}创建成功: ID {db_obj.id}")
        return db_obj
    
    def get(self, db: Session, id: Any, *, include_deleted: bool = False) -> Optional[ModelType]:
        """
        根据ID获取资源
        
        Args:
            db: 数据库会话
            id: 资源ID
            include_deleted: 是否包含已删除的资源
        
        Returns:
            资源对象或None
        """
        logger.debug(f"获取{self.resource_name}: ID {id}")
        
        query = db.query(self.model).filter(self.model.id == id)
        
        # 检查是否有软删除字段
        if hasattr(self.model, 'is_delete') and not include_deleted:
            query = query.filter(self.model.is_delete == False)
        
        return query.first()
    
    def get_multi(
        self, 
        db: Session, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        include_deleted: bool = False,
        filters: Optional[dict] = None
    ) -> List[ModelType]:
        """
        获取资源列表
        
        Args:
            db: 数据库会话
            skip: 跳过的数量
            limit: 限制数量
            include_deleted: 是否包含已删除的资源
            filters: 额外的过滤条件
        
        Returns:
            资源列表
        """
        logger.debug(f"获取{self.resource_name}列表: skip={skip}, limit={limit}")
        
        query = db.query(self.model)
        
        # 软删除过滤
        if hasattr(self.model, 'is_delete') and not include_deleted:
            query = query.filter(self.model.is_delete == False)
        
        # 应用额外过滤条件
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.filter(getattr(self.model, key) == value)
        
        return query.offset(skip).limit(limit).all()
    
    def update(
        self, 
        db: Session, 
        *, 
        db_obj: ModelType, 
        obj_in: UpdateSchemaType,
        **kwargs
    ) -> ModelType:
        """
        更新资源
        
        Args:
            db: 数据库会话
            db_obj: 数据库对象
            obj_in: 更新数据
            **kwargs: 额外的字段值
        
        Returns:
            更新后的资源对象
        """
        logger.info(f"更新{self.resource_name}: ID {db_obj.id}")
        
        # 获取更新数据
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True) if hasattr(obj_in, 'model_dump') else obj_in.dict(exclude_unset=True)
        
        # 添加额外字段
        update_data.update(kwargs)
        
        # 应用更新
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        
        db.commit()
        db.refresh(db_obj)
        
        logger.info(f"{self.resource_name}更新成功: ID {db_obj.id}")
        return db_obj
    
    def delete(self, db: Session, *, id: Any, soft_delete: bool = True) -> Optional[ModelType]:
        """
        删除资源
        
        Args:
            db: 数据库会话
            id: 资源ID
            soft_delete: 是否软删除
        
        Returns:
            删除的资源对象或None
        """
        logger.info(f"删除{self.resource_name}: ID {id}")
        
        db_obj = self.get(db, id)
        if not db_obj:
            logger.warning(f"{self.resource_name}不存在: ID {id}")
            return None
        
        if soft_delete and hasattr(db_obj, 'is_delete'):
            # 软删除
            db_obj.is_delete = True
            db.commit()
            logger.info(f"{self.resource_name}软删除成功: ID {id}")
        else:
            # 硬删除
            db.delete(db_obj)
            db.commit()
            logger.info(f"{self.resource_name}硬删除成功: ID {id}")
        
        return db_obj
    
    def exists(self, db: Session, *, filters: dict) -> bool:
        """
        检查资源是否存在
        
        Args:
            db: 数据库会话
            filters: 过滤条件
        
        Returns:
            是否存在
        """
        query = db.query(self.model)
        
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.filter(getattr(self.model, key) == value)
        
        # 排除软删除的记录
        if hasattr(self.model, 'is_delete'):
            query = query.filter(self.model.is_delete == False)
        
        return query.first() is not None
    
    def count(self, db: Session, *, filters: Optional[dict] = None, include_deleted: bool = False) -> int:
        """
        统计资源数量
        
        Args:
            db: 数据库会话
            filters: 过滤条件
            include_deleted: 是否包含已删除的资源
        
        Returns:
            资源数量
        """
        query = db.query(self.model)
        
        # 软删除过滤
        if hasattr(self.model, 'is_delete') and not include_deleted:
            query = query.filter(self.model.is_delete == False)
        
        # 应用过滤条件
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.filter(getattr(self.model, key) == value)
        
        return query.count()

# ====================
# 预定义服务类
# ====================

class UserService(BaseService):
    """用户服务类"""
    
    def __init__(self):
        from .models import User
        from .schemas import UserCreate, UserUpdate
        super().__init__(User, "用户")
    
    def get_by_username(self, db: Session, username: str) -> Optional[ModelType]:
        """根据用户名获取用户"""
        return db.query(self.model).filter(
            self.model.username == username,
            self.model.is_delete == False
        ).first()
    
    def get_by_email(self, db: Session, email: str) -> Optional[ModelType]:
        """根据邮箱获取用户"""
        return db.query(self.model).filter(
            self.model.email == email,
            self.model.is_delete == False
        ).first()

class LLMModelService(BaseService):
    """大模型服务类"""
    
    def __init__(self):
        from .models import LLMModel
        from .schemas import LLMModelCreate, LLMModelUpdate
        super().__init__(LLMModel, "大模型")
    
    def get_by_type(self, db: Session, model_type: str) -> List[ModelType]:
        """根据类型获取模型列表"""
        return db.query(self.model).filter(
            self.model.type == model_type,
            self.model.is_delete == False,
            self.model.is_active == True
        ).all()
    
    def get_by_name(self, db: Session, name: str) -> Optional[ModelType]:
        """根据名称获取模型"""
        return db.query(self.model).filter(
            self.model.name == name,
            self.model.is_delete == False
        ).first()

# 创建服务实例
user_service = UserService()
llm_model_service = LLMModelService()