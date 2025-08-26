from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from module.database import get_db
from module.schemas import LLMModelCreate, LLMModelUpdate, LLMModelOut
from module.llm_service import LLMService
from logger_config import get_logger

logger = get_logger("llm_api")
router = APIRouter(
    prefix="/llm",
    tags=["大模型管理"]
)

@router.post("/models", response_model=LLMModelOut)
def create_llm_model(llm_model: LLMModelCreate, db: Session = Depends(get_db)):
    """创建新的大模型配置"""
    logger.info(f"API请求: 创建大模型配置 {llm_model.name}")
    try:
        return LLMService.create_llm_model(db=db, llm_model=llm_model)
    except Exception as e:
        logger.error(f"创建大模型配置失败: {str(e)}")
        raise HTTPException(status_code=400, detail=f"创建大模型配置失败: {str(e)}")

@router.get("/models", response_model=List[LLMModelOut])
def read_llm_models(skip: int = 0, limit: int = 100, is_delete: bool = False, db: Session = Depends(get_db)):
    """获取大模型配置列表"""
    logger.info(f"API请求: 获取大模型配置列表，跳过: {skip}，限制: {limit}，已删除: {is_delete}")
    try:
        return LLMService.get_llm_models(db=db, skip=skip, limit=limit, is_delete=is_delete)
    except Exception as e:
        logger.error(f"获取大模型配置列表失败: {str(e)}")
        raise HTTPException(status_code=400, detail=f"获取大模型配置列表失败: {str(e)}")



@router.get("/models/{llm_model_id}", response_model=LLMModelOut)
def read_llm_model(llm_model_id: int, db: Session = Depends(get_db)):
    """根据ID获取大模型配置"""
    logger.info(f"API请求: 获取大模型配置ID: {llm_model_id}")
    db_llm_model = LLMService.get_llm_model(db=db, llm_model_id=llm_model_id)
    if db_llm_model is None:
        logger.error(f"大模型配置不存在: {llm_model_id}")
        raise HTTPException(status_code=404, detail="大模型配置不存在")
    return db_llm_model

@router.put("/models/{llm_model_id}", response_model=LLMModelOut)
def update_llm_model(llm_model_id: int, llm_model: LLMModelUpdate, db: Session = Depends(get_db)):
    """更新大模型配置"""
    logger.info(f"API请求: 更新大模型配置ID: {llm_model_id}")
    db_llm_model = LLMService.update_llm_model(db=db, llm_model_id=llm_model_id, llm_model=llm_model)
    if db_llm_model is None:
        logger.error(f"大模型配置不存在: {llm_model_id}")
        raise HTTPException(status_code=404, detail="大模型配置不存在")
    return db_llm_model

@router.delete("/models/{llm_model_id}", response_model=LLMModelOut)
def delete_llm_model(llm_model_id: int, db: Session = Depends(get_db)):
    """删除大模型配置（软删除）"""
    logger.info(f"API请求: 删除大模型配置ID: {llm_model_id}")
    db_llm_model = LLMService.delete_llm_model(db=db, llm_model_id=llm_model_id)
    if db_llm_model is None:
        logger.error(f"大模型配置不存在: {llm_model_id}")
        raise HTTPException(status_code=404, detail="大模型配置不存在")
    return db_llm_model

@router.get("/models/type/{model_type}", response_model=List[LLMModelOut])
def read_llm_models_by_type(model_type: str, db: Session = Depends(get_db)):
    """根据类型获取大模型配置"""
    logger.info(f"API请求: 获取大模型配置类型: {model_type}")
    try:
        return LLMService.get_llm_models_by_type(db=db, model_type=model_type)
    except Exception as e:
        logger.error(f"获取大模型配置类型失败: {str(e)}")
        raise HTTPException(status_code=400, detail=f"获取大模型配置类型失败: {str(e)}")