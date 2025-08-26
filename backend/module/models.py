"""
数据库模型定义

本模块定义了RAG系统的所有数据库模型，包括：
- 用户管理：User模型
- 大语言模型配置：LLMModel模型
- 文档管理：Document模型
- 问答历史：QAHistory模型
- 系统配置：SystemConfig模型

作者: RAG-System Team
版本: 1.0
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, Enum, Boolean
from sqlalchemy.orm import relationship
from .database import Base
from enum import Enum as PyEnum

# ====================
# 枚举类型定义
# ====================

class Role(PyEnum):
    """用户角色枚举"""
    admin = "admin"  # 管理员
    user = "user"    # 普通用户

class ModelType(PyEnum):
    """大语言模型类型枚举"""
    chat = "chat"            # 对话模型
    embedding = "embedding"  # 嵌入模型
    rerank = "rerank"        # 重排序模型

class ConfigType(PyEnum):
    """配置值类型枚举"""
    string = "string"    # 字符串类型
    integer = "integer"  # 整数类型
    float = "float"      # 浮点数类型
    boolean = "boolean"  # 布尔类型

# ====================
# 数据库表模型定义
# ====================

class LLMModel(Base):
    """
    大语言模型配置表
    
    用于存储系统中支持的各类AI模型的配置信息，
    包括API密钥、基础URL、模型参数等。
    """
    __tablename__ = "llm_models"
    
    id = Column(Integer, primary_key=True, index=True, comment="主键")
    name = Column(String(100), unique=True, index=True, comment="模型名称")
    type = Column(Enum(ModelType), comment="模型类型")
    api_key = Column(String(255), comment="API密钥")
    base_url = Column(String(255), comment="API基础URL")
    model_params = Column(Text, comment="模型参数JSON")
    is_active = Column(Boolean, default=True, comment="是否激活")
    is_delete = Column(Boolean, default=False, comment="是否已删除")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

class User(Base):
    """
    用户表
    
    存储系统用户的基本信息，包括认证信息和角色权限。
    支持逻辑删除机制。
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True, comment="用户ID")
    username = Column(String(50), unique=True, index=True, comment="用户名")
    email = Column(String(100), unique=True, index=True, comment="邮箱地址")
    hashed_password = Column(String(255), comment="加密密码哈希")
    phone = Column(String(20), comment="手机号码")
    role = Column(Enum(Role), default=Role.user, comment="用户角色")
    is_delete = Column(Boolean, default=False, index=True, comment="是否已删除")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")
    
    # 关联关系
    documents = relationship("Document", back_populates="owner", cascade="all, delete-orphan")
    qa_histories = relationship("QAHistory", back_populates="user", cascade="all, delete-orphan")

class Document(Base):
    """
    文档表
    
    存储用户上传的文档信息，包括文件路径和Milvus集合对应关系。
    支持逻辑删除机制。
    """
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True, comment="文档ID")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, comment="用户ID")
    original_filename = Column(String(255), comment="原始文件名")
    stored_path = Column(String(255), comment="存储路径")
    milvus_collection_name = Column(String(100), index=True, comment="Milvus集合名")
    status = Column(String(20), default="pending", index=True, comment="处理状态（pending,processing,processed,failed）")
    error_message = Column(String(255), nullable=True, comment="错误信息")
    is_delete = Column(Boolean, default=False, index=True, comment="是否已删除")
    uploaded_at = Column(DateTime, default=datetime.now, comment="上传时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")
    
    # 关联关系
    owner = relationship("User", back_populates="documents")

class QAHistory(Base):
    """
    问答历史表
    
    存储用户与系统的问答交互历史，用于历史查询和数据分析。
    """
    __tablename__ = "qa_history"
    
    id = Column(Integer, primary_key=True, index=True, comment="历史记录ID")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, comment="用户ID")
    question = Column(Text, comment="用户问题")
    answer = Column(Text, comment="系统回答")
    asked_at = Column(DateTime, default=datetime.now, index=True, comment="问问时间")
    
    # 关联关系
    user = relationship("User", back_populates="qa_histories")

class SystemConfig(Base):
    """
    系统配置表
    
    存储系统级配置信息，包括安全配置、系统参数等。
    支持动态配置和敏感信息保护。
    """
    __tablename__ = "system_configs"
    
    id = Column(Integer, primary_key=True, index=True, comment="配置ID")
    config_key = Column(String(100), unique=True, index=True, comment="配置键名")
    config_value = Column(Text, comment="配置值")
    config_type = Column(String(20), default="string", comment="配置值类型")
    description = Column(String(255), comment="配置描述")
    is_sensitive = Column(Boolean, default=False, index=True, comment="是否为敏感信息")
    is_active = Column(Boolean, default=True, index=True, comment="是否启用")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")