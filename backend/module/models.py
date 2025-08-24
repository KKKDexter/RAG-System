from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, Enum
from sqlalchemy.orm import relationship
from database import Base
from enum import Enum as PyEnum

# 用户角色枚举
class Role(PyEnum):
    admin = "admin"
    user = "user"

# 数据库表定义
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(100))
    phone = Column(String(20))
    role = Column(Enum(Role), default=Role.user)
    created_at = Column(DateTime, default=datetime.now)
    
    documents = relationship("Document", back_populates="owner")
    qa_histories = relationship("QAHistory", back_populates="user")

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    original_filename = Column(String(255))
    stored_path = Column(String(255))
    milvus_collection_name = Column(String(100))
    uploaded_at = Column(DateTime, default=datetime.now)
    
    owner = relationship("User", back_populates="documents")

class QAHistory(Base):
    __tablename__ = "qa_history"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    question = Column(Text)
    answer = Column(Text)
    asked_at = Column(DateTime, default=datetime.now)
    
    user = relationship("User", back_populates="qa_histories")