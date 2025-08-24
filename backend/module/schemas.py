from typing import List, Optional, Dict
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from .models import Role, ModelType

# 用户相关模型
class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    phone: Optional[str] = None
    role: Optional[Role] = Role.user

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[Role] = None

class UserOut(BaseModel):
    id: int
    username: str
    email: str
    phone: Optional[str] = None
    role: Role
    is_delete: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# 认证相关模型
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str

# 文档相关模型
class DocumentUpdate(BaseModel):
    original_filename: Optional[str] = None

class DocumentOut(BaseModel):
    id: int
    user_id: int
    original_filename: str
    is_delete: bool
    uploaded_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

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
    
    model_config = ConfigDict(from_attributes=True)

# 问答相关模型
class AskRequest(BaseModel):
    question: str
    chat_model_id: Optional[int] = None  # 可选的Chat模型ID
    embedding_model_id: Optional[int] = None  # 可选的Embedding模型ID

class AskResponse(BaseModel):
    answer: str