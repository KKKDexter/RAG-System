from sqlalchemy.orm import Session
from .models import LLMModel
from .schemas import LLMModelCreate, LLMModelUpdate
from logger_config import get_logger

logger = get_logger("llm_service")

class LLMService:
    @staticmethod
    def create_llm_model(db: Session, llm_model: LLMModelCreate):
        """创建新的大模型配置"""
        logger.info(f"创建大模型配置: {llm_model.name}")
        db_llm_model = LLMModel(
            name=llm_model.name,
            type=llm_model.type,
            api_key=llm_model.api_key,
            base_url=llm_model.base_url,
            model_params=str(llm_model.model_params) if llm_model.model_params else None,
            is_active=llm_model.is_active
        )
        db.add(db_llm_model)
        db.commit()
        db.refresh(db_llm_model)
        logger.info(f"大模型配置创建成功: {db_llm_model.id}")
        return db_llm_model

    @staticmethod
    def get_llm_models(db: Session, skip: int = 0, limit: int = 100, is_delete: bool = False):
        """获取大模型配置列表"""
        logger.info(f"获取大模型配置列表，跳过: {skip}，限制: {limit}，已删除: {is_delete}")
        return db.query(LLMModel).filter(LLMModel.is_delete == is_delete).offset(skip).limit(limit).all()

    @staticmethod
    def get_llm_model(db: Session, llm_model_id: int):
        """根据ID获取大模型配置"""
        logger.info(f"获取大模型配置ID: {llm_model_id}")
        return db.query(LLMModel).filter(LLMModel.id == llm_model_id, LLMModel.is_delete == False).first()

    @staticmethod
    def update_llm_model(db: Session, llm_model_id: int, llm_model: LLMModelUpdate):
        """更新大模型配置"""
        logger.info(f"更新大模型配置ID: {llm_model_id}")
        db_llm_model = db.query(LLMModel).filter(LLMModel.id == llm_model_id, LLMModel.is_delete == False).first()
        if db_llm_model:
            if llm_model.name is not None:
                db_llm_model.name = llm_model.name
            if llm_model.type is not None:
                db_llm_model.type = llm_model.type
            if llm_model.api_key is not None:
                db_llm_model.api_key = llm_model.api_key
            if llm_model.base_url is not None:
                db_llm_model.base_url = llm_model.base_url
            if llm_model.model_params is not None:
                db_llm_model.model_params = str(llm_model.model_params)
            if llm_model.is_active is not None:
                db_llm_model.is_active = llm_model.is_active
            db.commit()
            db.refresh(db_llm_model)
            logger.info(f"大模型配置更新成功: {llm_model_id}")
        return db_llm_model

    @staticmethod
    def delete_llm_model(db: Session, llm_model_id: int):
        """删除大模型配置（软删除）"""
        logger.info(f"删除大模型配置ID: {llm_model_id}")
        db_llm_model = db.query(LLMModel).filter(LLMModel.id == llm_model_id, LLMModel.is_delete == False).first()
        if db_llm_model:
            db_llm_model.is_delete = True
            db.commit()
            logger.info(f"大模型配置删除成功: {llm_model_id}")
        return db_llm_model

    @staticmethod
    def get_llm_models_by_type(db: Session, model_type: str):
        """根据类型获取大模型配置"""
        logger.info(f"获取大模型配置类型: {model_type}")
        return db.query(LLMModel).filter(LLMModel.type == model_type, LLMModel.is_delete == False, LLMModel.is_active == True).all()