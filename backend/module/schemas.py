"""
Pydantic模型定义

本模块定义了API输入输出数据的验证和序列化模型，包括：
- 用户管理相关模型
- 认证相关模型
- 文档管理相关模型
- 大语言模型配置相关模型
- 系统配置相关模型

作者: RAG-System Team
版本: 1.0
"""

from typing import List, Optional, Dict
from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from .models import Role, ModelType, ConfigType

# ====================
# 用户相关模型
# ====================

class UserCreate(BaseModel):
    """用户创建模型"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名，3-50个字符")
    email: str = Field(..., description="邮箱地址")
    password: str = Field(..., min_length=8, description="密码，至少8个字符")
    phone: Optional[str] = Field(None, max_length=20, description="手机号码")
    role: Optional[Role] = Field(Role.user, description="用户角色")

class UserUpdate(BaseModel):
    """用户更新模型"""
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="用户名")
    email: Optional[str] = Field(None, description="邮箱地址")
    password: Optional[str] = Field(None, min_length=8, description="密码")
    phone: Optional[str] = Field(None, max_length=20, description="手机号码")
    role: Optional[Role] = Field(None, description="用户角色")

class UserOut(BaseModel):
    """用户输出模型（不包含敏感信息）"""
    id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    email: str = Field(..., description="邮箱地址")
    phone: Optional[str] = Field(None, description="手机号码")
    role: Role = Field(..., description="用户角色")
    is_delete: bool = Field(..., description="是否已删除")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
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
    status: str
    error_message: Optional[str] = None
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
    # 注意：api_key出于安全考虑不在输出中暴露
    
    model_config = ConfigDict(from_attributes=True)

# 问答相关模型
class AskRequest(BaseModel):
    question: str
    chat_model_id: Optional[str] = None  # 可选的Chat模型ID或名称
    embedding_model_id: Optional[str] = None  # 可选的Embedding模型ID或名称

class AskResponse(BaseModel):
    answer: str

# 系统配置相关模型
class SystemConfigCreate(BaseModel):
    config_key: str
    config_value: str
    config_type: Optional[ConfigType] = ConfigType.string
    description: Optional[str] = None
    is_sensitive: Optional[bool] = False
    is_active: Optional[bool] = True

class SystemConfigUpdate(BaseModel):
    config_value: Optional[str] = None
    config_type: Optional[ConfigType] = None
    description: Optional[str] = None
    is_sensitive: Optional[bool] = None
    is_active: Optional[bool] = None

class SystemConfigOut(BaseModel):
    id: int
    config_key: str
    config_value: Optional[str] = None  # 敏感信息可能隐藏
    config_type: ConfigType
    description: Optional[str] = None
    is_sensitive: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)