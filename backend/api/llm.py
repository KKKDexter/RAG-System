"""
大语言模型管理 API

本模块提供大语言模型配置的CRUD操作接口，
支持chat、embedding、rerank等类型的模型管理。

作者: RAG-System Team
版本: 2.0
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from module.database import get_db
from module.schemas import LLMModelCreate, LLMModelUpdate, LLMModelOut
from module.llm_service import LLMService
from module.exception_handler import (
    create_resource, update_resource, delete_resource, get_resource,
    raise_not_found
)
from logger_config import get_logger

logger = get_logger("llm_api")

# 创建路由器
router = APIRouter(
    prefix="/llm",
    tags=["大模型管理"]
)

@router.post("/models", response_model=LLMModelOut)
@create_resource("大模型配置")
def create_llm_model(llm_model: LLMModelCreate, db: Session = Depends(get_db)):
    """创建新的大模型配置"""
    logger.info(f"API请求: 创建大模型配置 {llm_model.name}")
    return LLMService.create_llm_model(db=db, llm_model=llm_model)

@router.get("/models", response_model=List[LLMModelOut])
@get_resource("大模型配置列表")
def read_llm_models(skip: int = 0, limit: int = 100, is_delete: bool = False, db: Session = Depends(get_db)):
    """获取大模型配置列表"""
    logger.info(f"API请求: 获取大模型配置列表，跳过: {skip}，限制: {limit}，已删除: {is_delete}")
    return LLMService.get_llm_models(db=db, skip=skip, limit=limit, is_delete=is_delete)

@router.get("/models/{llm_model_id}", response_model=LLMModelOut)
@get_resource("大模型配置")
def read_llm_model(llm_model_id: int, db: Session = Depends(get_db)):
    """根据ID获取大模型配置"""
    logger.info(f"API请求: 获取大模型配置ID: {llm_model_id}")
    db_llm_model = LLMService.get_llm_model(db=db, llm_model_id=llm_model_id)
    if db_llm_model is None:
        raise_not_found("大模型配置", llm_model_id)
    return db_llm_model

@router.put("/models/{llm_model_id}", response_model=LLMModelOut)
@update_resource("大模型配置")
def update_llm_model(llm_model_id: int, llm_model: LLMModelUpdate, db: Session = Depends(get_db)):
    """更新大模型配置"""
    logger.info(f"API请求: 更新大模型配置ID: {llm_model_id}")
    db_llm_model = LLMService.update_llm_model(db=db, llm_model_id=llm_model_id, llm_model=llm_model)
    if db_llm_model is None:
        raise_not_found("大模型配置", llm_model_id)
    return db_llm_model

@router.delete("/models/{llm_model_id}", response_model=LLMModelOut)
@delete_resource("大模型配置")
def delete_llm_model(llm_model_id: int, db: Session = Depends(get_db)):
    """删除大模型配置（软删除）"""
    logger.info(f"API请求: 删除大模型配置ID: {llm_model_id}")
    db_llm_model = LLMService.delete_llm_model(db=db, llm_model_id=llm_model_id)
    if db_llm_model is None:
        raise_not_found("大模型配置", llm_model_id)
    return db_llm_model

@router.get("/models/type/{model_type}", response_model=List[LLMModelOut])
@get_resource("按类型查询大模型")
def read_llm_models_by_type(model_type: str, db: Session = Depends(get_db)):
    """根据类型获取大模型配置"""
    logger.info(f"API请求: 获取大模型配置类型: {model_type}")
    return LLMService.get_llm_models_by_type(db=db, model_type=model_type)