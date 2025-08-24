from typing import List, Optional, Dict
from datetime import datetime
from pydantic import BaseModel
from .models import Role, ModelType

# 用户相关模型
class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    phone: Optional[str] = None
    role: Optional[Role] = Role.user

class UserOut(BaseModel):
    id: int
    username: str
    email: str
    role: Role
    
    class Config:
        orm_mode = True

# 认证相关模型
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# 文档相关模型
class DocumentOut(BaseModel):
    id: int
    original_filename: str
    uploaded_at: datetime
    
    class Config:
        orm_mode = True

# 大模型相关模型
class LLMModelCreate(BaseModel):
    name: str
    type: ModelType
    api_key: str
    base_url: str
    model_params: Optional[Dict] = None
    is_active: Optional[bool] = True

class LLMModelUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[ModelType] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model_params: Optional[Dict] = None
    is_active: Optional[bool] = None

class LLMModelOut(BaseModel):
    id: int
    name: str
    type: ModelType
    base_url: str
    is_active: bool
    is_delete: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

# 问答相关模型
class AskRequest(BaseModel):
    question: str

class AskResponse(BaseModel):
    answer: str