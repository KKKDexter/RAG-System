"""
大语言模型服务模块

本模块提供大语言模型配置的业务逻辑处理

作者: RAG-System Team
版本: 2.0
"""

from sqlalchemy.orm import Session
from typing import List, Optional
from .base_service import llm_model_service
from .models import LLMModel
from .schemas import LLMModelCreate, LLMModelUpdate
from logger_config import get_logger

logger = get_logger("llm_service")

class LLMService:
    """
    大语言模型服务类
    
    使用基类提供的通用CRUD操作，减少重复代码
    """
    
    @staticmethod
    def create_llm_model(db: Session, llm_model: LLMModelCreate) -> LLMModel:
        """创建新的大模型配置"""
        # 检查名称是否已存在
        if llm_model_service.get_by_name(db, llm_model.name):
            raise ValueError(f"模型名称 '{llm_model.name}' 已存在")
        
        # 处理模型参数
        model_params_str = None
        if llm_model.model_params:
            model_params_str = str(llm_model.model_params)
        
        return llm_model_service.create(
            db, 
            obj_in=llm_model,
            model_params=model_params_str
        )
    
    @staticmethod
    def get_llm_models(
        db: Session, 
        skip: int = 0, 
        limit: int = 100, 
        is_delete: bool = False
    ) -> List[LLMModel]:
        """获取大模型配置列表"""
        return llm_model_service.get_multi(
            db, 
            skip=skip, 
            limit=limit, 
            include_deleted=is_delete
        )
    
    @staticmethod
    def get_llm_model(db: Session, llm_model_id: int) -> Optional[LLMModel]:
        """根据ID获取大模型配置"""
        return llm_model_service.get(db, llm_model_id)
    
    @staticmethod
    def update_llm_model(
        db: Session, 
        llm_model_id: int, 
        llm_model: LLMModelUpdate
    ) -> Optional[LLMModel]:
        """更新大模型配置"""
        db_model = llm_model_service.get(db, llm_model_id)
        if not db_model:
            return None
        
        # 检查名称冲突
        if llm_model.name and llm_model.name != db_model.name:
            existing = llm_model_service.get_by_name(db, llm_model.name)
            if existing and existing.id != llm_model_id:
                raise ValueError(f"模型名称 '{llm_model.name}' 已存在")
        
        # 处理模型参数
        update_data = {}
        if llm_model.model_params is not None:
            update_data['model_params'] = str(llm_model.model_params)
        
        return llm_model_service.update(
            db,
            db_obj=db_model,
            obj_in=llm_model,
            **update_data
        )
    
    @staticmethod
    def delete_llm_model(db: Session, llm_model_id: int) -> Optional[LLMModel]:
        """删除大模型配置（软删除）"""
        return llm_model_service.delete(db, id=llm_model_id, soft_delete=True)
    
    @staticmethod
    def get_llm_models_by_type(db: Session, model_type: str) -> List[LLMModel]:
        """根据类型获取大模型配置"""
        return llm_model_service.get_by_type(db, model_type)
    
    @staticmethod
    def get_llm_model_by_name(db: Session, model_name: str) -> Optional[LLMModel]:
        """根据名称获取大模型配置"""
        return llm_model_service.get_by_name(db, model_name)