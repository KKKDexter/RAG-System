import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from module.database import get_db
from module.models import Document, User, QAHistory
from module.schemas import DocumentOut, AskRequest, AskResponse
from module.auth_service import get_current_active_user
import asyncio
import os

# 根据环境变量动态导入配置
env = os.environ.get('ENVIRONMENT', 'dev')
if env == 'prod':
    from config.prod import VECTOR_DIM, EMBEDDING_MODEL_API_KEY, EMBEDDING_MODEL_NAME, EMBEDDING_MODEL_URL, CHAT_MODEL_API_KEY, CHAT_MODEL_NAME, CHAT_MODEL_URL
else:
    from config.dev import VECTOR_DIM, EMBEDDING_MODEL_API_KEY, EMBEDDING_MODEL_NAME, EMBEDDING_MODEL_URL, CHAT_MODEL_API_KEY, CHAT_MODEL_NAME, CHAT_MODEL_URL

# 尝试导入可选依赖
try:
    from module.milvus_service import search_similar_vectors
    MILVUS_AVAILABLE = True
except ImportError as e:
    print(f"[WARNING] Milvus服务不可用: {e}")
    MILVUS_AVAILABLE = False

try:
    from module.document_service import process_document, save_uploaded_file, get_storage_dir
    DOCUMENT_SERVICE_AVAILABLE = True
except ImportError as e:
    print(f"[WARNING] 文档服务不可用: {e}")
    DOCUMENT_SERVICE_AVAILABLE = False
    
    # 定义mock函数，在文档服务不可用时使用
    async def save_uploaded_file(file, storage_type=None, folder_path="documents"):
        """Mock 函数：文档上传服务不可用时返回错误信息"""
        # 创建一个临时路径结果，避免立即抛出异常
        import tempfile
        import uuid
        temp_dir = tempfile.gettempdir()
        temp_filename = f"{uuid.uuid4()}_{file.filename}"
        temp_path = os.path.join(temp_dir, temp_filename)
        
        # 保存文件到临时位置
        with open(temp_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        return {
            "local_path": temp_path,
            "minio_path": None,
            "file_extension": os.path.splitext(file.filename)[1].lower(),
            "status": "mock_upload",
            "message": "文档服务依赖缺失，使用临时存储"
        }
    
    def process_document(*args, **kwargs):
        """Mock 函数：文档处理服务不可用时使用占位符"""
        # 返回一些占位符数据而不是抛出异常
        from collections import namedtuple
        
        # 创建简单的文本对象
        MockText = namedtuple('MockText', ['page_content'])
        mock_texts = [MockText(page_content="文档处理服务不可用，请安装缺失的依赖")]
        
        # 创建简单的embeddings对象
        class MockEmbeddings:
            def embed_query(self, text):
                # 返回固定维度的占位符向量
                return [0.1] * VECTOR_DIM
        
        return mock_texts, MockEmbeddings()
    
    def get_storage_dir(folder_path="documents"):
        """Mock 函数：返回临时存储目录"""
        import tempfile
        return os.path.join(tempfile.gettempdir(), folder_path)

try:
    from module.storage_service import get_storage_service_info
    STORAGE_SERVICE_AVAILABLE = True
except ImportError as e:
    print(f"[WARNING] 存储服务不可用: {e}")
    STORAGE_SERVICE_AVAILABLE = False
    
    def get_storage_service_info():
        """Mock 函数，在存储服务不可用时使用"""
        return {
            "available_modes": ["local"],
            "current_mode": "local",
            "storage_info": {
                "local": {"status": "available"},
                "minio": {"status": "unavailable", "reason": "MinIO依赖缺失"}
            }
        }

try:
    from module.redis_service import cache_qa_result, get_cached_qa_result
    REDIS_AVAILABLE = True
except ImportError as e:
    print(f"[WARNING] Redis服务不可用: {e}")
    REDIS_AVAILABLE = False
    
    def cache_qa_result(*args, **kwargs):
        """Mock 函数，在Redis不可用时使用"""
        pass  # 不做任何缓存操作
    
    def get_cached_qa_result(*args, **kwargs):
        """Mock 函数，在Redis不可用时使用"""
        return None  # 始终返回缓存未命中

try:
    from langchain_community.embeddings import OpenAIEmbeddings
    from langchain_community.chat_models import ChatOpenAI
    LANGCHAIN_AVAILABLE = True
except ImportError as e:
    print(f"[WARNING] LangChain不可用: {e}")
    LANGCHAIN_AVAILABLE = False

# 导入日志配置
from logger_config import get_logger
logger = get_logger("rag_router")

# 创建路由
router = APIRouter(
    prefix="/v1/rag",
    tags=["RAG"],
)

# 异步处理文档
async def process_document_async(document_id: int, storage_result: dict, embedding_model_id: str, user_id: int, db_session: Session):
    """
    异步处理文档，包括文本分割、向量生成和存储到Milvus
    
    Args:
        document_id: 文档ID
        storage_result: 存储结果信息
        embedding_model_id: 指定的embedding模型ID
        user_id: 用户ID
        db_session: 数据库会话（不使用，重新创建）
    """
    # 声明全局变量
    global VECTOR_DIM
    
    # 创建新的数据库会话，避免异步问题
    from module.database import SessionLocal
    new_db_session = SessionLocal()
    
    try:
        logger.info(f"开始异步处理文档 ID: {document_id}")
        
        # 查询文档
        document = new_db_session.query(Document).filter(Document.id == document_id).first()
        if not document:
            logger.error(f"找不到文档 ID: {document_id}")
            return
        
        # 更新文档状态为处理中
        document.status = "processing"
        new_db_session.commit()
        logger.info(f"文档 {document_id} 状态更新为: processing")
        
        # 检查是否有必要的依赖
        if not DOCUMENT_SERVICE_AVAILABLE:
            logger.warning(f"文档服务不可用，将使用mock处理，文档ID: {document_id}")
            
        if not MILVUS_AVAILABLE:
            logger.warning(f"Milvus服务不可用，跳过向量存储，文档ID: {document_id}")
            # 直接标记为已处理（但没有实际处理）
            document.status = "processed"
            document.error_message = "Milvus服务不可用，文档已上传但未生成向量索引"
            new_db_session.commit()
            return
        
        # 处理文档
        logger.info(f"开始处理文档内容: {document.original_filename}")
        if storage_result.get("local_path"):
            # 从本地路径处理
            texts, embeddings = process_document(
                file_path=storage_result["local_path"], 
                file_extension=storage_result["file_extension"],
                embedding_model_name=embedding_model_id  # 传递embedding模型名称
            )
        elif storage_result.get("minio_path"):
            # 从Minio路径处理
            texts, embeddings = process_document(
                minio_path=storage_result["minio_path"], 
                file_extension=storage_result["file_extension"],
                embedding_model_name=embedding_model_id  # 传递embedding模型名称
            )
        else:
            logger.error(f"文档 {document_id} 没有有效的存储路径")
            document.status = "failed"
            document.error_message = "文档没有有效的存储路径"
            new_db_session.commit()
            return
            
        logger.info(f"文档内容处理完成，得到 {len(texts)} 个文本块")
        
        # 如果Milvus不可用，跳过向量处理
        if not MILVUS_AVAILABLE:
            logger.info(f"Milvus不可用，跳过向量处理，文档ID: {document_id}")
            document.status = "processed"
            document.error_message = "Milvus服务不可用，文档已处理但未生成向量索引"
            new_db_session.commit()
            return
        
        # 获取用户的Milvus集合
        logger.debug(f"加载Milvus集合: {document.milvus_collection_name}")
        try:
            from pymilvus import Collection
            from module.milvus_service import create_user_collection
            
            # 首先生成一个测试向量来检测维度
            actual_vector_dim = VECTOR_DIM  # 默认维度
            
            if len(texts) > 0:
                try:
                    logger.debug("生成测试向量来检测维度")
                    test_vector = embeddings.embed_query("测试文本")
                    if isinstance(test_vector, list) and len(test_vector) > 0:
                        actual_vector_dim = len(test_vector)
                        logger.info(f"检测到实际向量维度: {actual_vector_dim}")
                        
                        # 更新全局维度配置
                        VECTOR_DIM = actual_vector_dim
                        logger.info(f"更新全局VECTOR_DIM为: {VECTOR_DIM}")
                    else:
                        logger.warning(f"测试向量格式异常: {type(test_vector)}")
                except Exception as test_error:
                    logger.warning(f"测试向量生成失败: {str(test_error)}，使用默认维度")
            
            # 使用实际维度创建或检查集合
            collection_name = create_user_collection(user_id, actual_vector_dim)
            collection = Collection(name=collection_name)
            collection.load()
            logger.info(f"Milvus集合加载成功: {collection_name}，维度: {actual_vector_dim}")
        except Exception as milvus_error:
            logger.error(f"Milvus集合操作失败: {str(milvus_error)}")
            document.status = "failed"
            document.error_message = f"Milvus集合操作失败: {str(milvus_error)[:200]}"
            new_db_session.commit()
            return
        
        # 准备数据
        logger.debug(f"为文档 {document_id} 准备向量数据")
        vectors = []
        contents = []
        document_ids = []
        
        for text in texts:
            # 尝试生成实际向量，失败时记录错误
            try:
                logger.debug(f"开始为文本块生成向量: {text.page_content[:50]}...")
                
                # 直接调用embedding模型，不使用复杂的异步包装
                vector = embeddings.embed_query(text.page_content)
                
                # 验证向量维度
                if isinstance(vector, list) and len(vector) > 0:
                    logger.debug(f"成功为文本生成向量，维度: {len(vector)}")
                    vectors.append(vector)
                    contents.append(text.page_content)
                    document_ids.append(document_id)
                else:
                    logger.error(f"生成的向量格式错误: {type(vector)}, 长度: {len(vector) if hasattr(vector, '__len__') else 'N/A'}")
                    # 跳过这个文本块
                    continue
                    
            except Exception as e:
                logger.error(f"向量生成失败: {str(e)}")
                logger.error(f"错误详情: {type(e).__name__}")
                
                # 对于Ollama模型，尝试不同的调用方式
                if "nomic" in str(embedding_model_id).lower() or "ollama" in str(type(embeddings)).lower():
                    try:
                        logger.info("尝试使用简化的Ollama调用方式")
                        # 简化调用，避免复杂参数
                        vector = embeddings.embed_query(text.page_content[:1000])  # 限制文本长度
                        if isinstance(vector, list) and len(vector) > 0:
                            logger.info(f"Ollama简化调用成功，向量维度: {len(vector)}")
                            vectors.append(vector)
                            contents.append(text.page_content)
                            document_ids.append(document_id)
                            continue
                    except Exception as retry_error:
                        logger.error(f"Ollama简化调用也失败: {str(retry_error)}")
                
                # 如果向量生成彻底失败，记录错误但继续处理其他文本
                logger.warning(f"跳过向量生成失败的文本块: {text.page_content[:100]}...")
        
        # 检查是否有有效的向量数据
        if not vectors or len(vectors) == 0:
            logger.error(f"文档 {document_id} 没有生成任何有效的向量数据")
            document.status = "failed"
            document.error_message = "向量生成失败，无法处理文档内容"
            new_db_session.commit()
            return
            
        logger.info(f"文档 {document_id} 成功生成了 {len(vectors)} 个向量")
        
        # 插入数据
        logger.debug(f"向Milvus集合中插入 {len(vectors)} 条向量数据")
        try:
            collection.insert([document_ids, contents, vectors])
            collection.flush()
            logger.info(f"成功插入 {len(vectors)} 条向量数据到Milvus")
        except Exception as insert_error:
            logger.error(f"向量数据插入失败: {str(insert_error)}")
            document.status = "failed"
            document.error_message = f"向量数据插入失败: {str(insert_error)[:200]}"
            new_db_session.commit()
            return
        
        # 更新文档状态为已处理
        document.status = "processed"
        document.error_message = None  # 清除错误信息
        new_db_session.commit()
        
        logger.info(f"文档 {document_id} 异步处理完成")
    except Exception as e:
        logger.error(f"异步处理文档 {document_id} 失败: {str(e)}")
        try:
            # 更新文档状态为处理失败
            document = new_db_session.query(Document).filter(Document.id == document_id).first()
            if document:
                document.status = "failed"
                document.error_message = str(e)[:255]
                new_db_session.commit()
        except Exception as update_error:
            logger.error(f"更新文档状态失败: {str(update_error)}")
    finally:
        # 关闭数据库会话
        new_db_session.close()

# 获取可用的embedding模型列表
@router.get("/embedding-models")
def get_embedding_models(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    获取可用的embedding模型列表，优先从数据库获取，如果没有则从配置中获取
    """
    logger.info(f"用户 {current_user.id} 请求获取embedding模型列表")
    
    try:
        # 尝试从数据库获取embedding模型列表
        from module.llm_service import LLMService
        db_models = LLMService.get_llm_models_by_type(db=db, model_type="embedding")
        
        # 创建前端需要的模型格式
        models = []
        
        # 添加数据库中的模型
        if db_models:
            for model in db_models:
                models.append({
                    "id": model.name,  # 前端需要id字段
                    "name": model.name,
                    "provider": "DB",
                    "description": f"数据库配置的模型: {model.name}",
                    "is_local": False  # 前端需要is_local字段
                })
                
        # 如果数据库中没有模型或者很少，添加默认的OpenAI模型
        if not models or len(models) < 1:
            models.append({
                "id": "text-embedding-ada-002",  # 前端需要id字段
                "name": "text-embedding-ada-002",
                "provider": "OpenAI",
                "description": "OpenAI的text-embedding-ada-002模型",
                "is_local": False  # 前端需要is_local字段
            })
        
        # 如果环境变量中有配置，也添加进去
        if EMBEDDING_MODEL_NAME and EMBEDDING_MODEL_NAME != "text-embedding-ada-002" and not any(m["id"] == EMBEDDING_MODEL_NAME for m in models):
            models.append({
                "id": EMBEDDING_MODEL_NAME,  # 前端需要id字段
                "name": EMBEDDING_MODEL_NAME,
                "provider": "ENV",
                "description": f"环境变量配置的模型: {EMBEDDING_MODEL_NAME}",
                "is_local": False  # 前端需要is_local字段
            })
        
        logger.info(f"成功获取embedding模型列表，共 {len(models)} 个模型")
        return models  # 直接返回数组，不包装在models字段中
    except Exception as e:
        logger.error(f"获取embedding模型列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取embedding模型列表失败: {str(e)}")

# 上传文档
@router.post("/upload", response_model=DocumentOut)
async def upload_document(
    file: UploadFile = File(...),
    storage_type: Optional[str] = Form(None),  # 新增存储类型参数
    embedding_model_id: Optional[str] = Form(None),  # 添加embedding模型ID参数
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    logger.info(f"用户 {current_user.id} 上传文档: {file.filename}，存储类型: {storage_type}，embedding模型: {embedding_model_id}")
    
    try:
        # 保存文件到指定存储
        logger.debug(f"保存上传文件: {file.filename}")
        storage_result = await save_uploaded_file(file, storage_type, "documents")
        
        # 创建文档记录
        logger.debug(f"创建文档数据库记录: {file.filename}")
        document = Document(
            user_id=current_user.id,
            original_filename=file.filename,
            stored_path=storage_result.get("local_path"),  # 本地路径（可能为None）
            milvus_collection_name=f"docs_user_{current_user.id}",
            status="pending"  # 假设Document模型有status字段
        )
        
        # 如果是MinIO存储，将MinIO路径存储在额外字段中
        if storage_result.get("minio_path"):
            if not storage_result.get("local_path"):
                document.stored_path = f"minio://{storage_result.get('minio_path')}"
        
        db.add(document)
        db.commit()
        db.refresh(document)
        logger.info(f"文档记录创建成功，文档ID: {document.id}")
        
        # 启动异步任务处理文档，但不等待其完成
        import asyncio
        asyncio.create_task(process_document_async(
            document_id=document.id,
            storage_result=storage_result,
            embedding_model_id=embedding_model_id,
            user_id=current_user.id,
            db_session=db
        ))
        
        return document
    except Exception as e:
        # 删除已保存的文件和文档记录
        logger.error(f"文档上传处理失败: {str(e)}")
        # 这里需要根据存储结果来清理文件
        if 'storage_result' in locals():
            try:
                # 检查是否有存储服务可用
                if STORAGE_SERVICE_AVAILABLE:
                    from module.storage_service import delete_file_from_storage
                    delete_file_from_storage(
                        storage_result.get("local_path"),
                        storage_result.get("minio_path")
                    )
                else:
                    # 手动清理本地临时文件
                    local_path = storage_result.get("local_path")
                    if local_path and os.path.exists(local_path):
                        os.remove(local_path)
                        logger.info(f"已清理临时文件: {local_path}")
            except Exception as cleanup_error:
                logger.error(f"清理存储文件失败: {str(cleanup_error)}")
        
        if 'document' in locals():
            try:
                db.delete(document)
                db.commit()
            except Exception as db_error:
                logger.error(f"删除文档记录失败: {str(db_error)}")
        raise HTTPException(status_code=500, detail=f"文档处理失败: {str(e)}")

# 获取存储服务信息
@router.get("/storage-info")
def get_storage_info(
    current_user: User = Depends(get_current_active_user)
):
    logger.info(f"用户 {current_user.id} 请求获取存储服务信息")
    try:
        storage_info = get_storage_service_info()
        logger.info(f"成功获取存储服务信息")
        return storage_info
    except Exception as e:
        logger.error(f"获取存储服务信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取存储服务信息失败: {str(e)}")

# 获取用户文档列表
@router.get("/documents", response_model=List[DocumentOut])
def get_documents(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    logger.info(f"用户 {current_user.id} 请求获取文档列表")
    try:
        documents = db.query(Document).filter(Document.user_id == current_user.id).all()
        logger.info(f"成功获取用户 {current_user.id} 的文档列表，共 {len(documents)} 个文档")
        logger.debug(f"文档列表: {[doc.original_filename for doc in documents]}")
        return documents
    except Exception as e:
        logger.error(f"获取文档列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取文档列表失败: {str(e)}")

# 获取单个文档
@router.get("/documents/{document_id}", response_model=DocumentOut)
def get_document(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    获取单个文档信息
    """
    logger.info(f"用户 {current_user.id} 请求获取文档 {document_id}")
    
    # 查找文档
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()
    
    if not document:
        logger.warning(f"文档 {document_id} 不存在或用户 {current_user.id} 无权访问")
        raise HTTPException(status_code=404, detail="文档不存在")
    
    logger.info(f"成功获取文档 {document_id}")
    return document

# 更新文档信息
@router.put("/documents/{document_id}", response_model=DocumentOut)
def update_document(
    document_id: int,
    document_data: DocumentOut,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    更新文档信息
    """
    logger.info(f"用户 {current_user.id} 请求更新文档 {document_id} 的信息")
    
    # 查找文档
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()
    
    if not document:
        logger.warning(f"文档 {document_id} 不存在或用户 {current_user.id} 无权访问")
        raise HTTPException(status_code=404, detail="文档不存在")
    
    try:
        # 更新文档信息
        document.original_filename = document_data.original_filename
        # 注意：这里不更新stored_path，因为文件路径不应该被随意更改
        
        db.commit()
        db.refresh(document)
        
        logger.info(f"用户 {current_user.id} 成功更新文档 {document_id} 的信息")
        return document
    except Exception as e:
        logger.error(f"更新文档信息失败: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新文档信息失败: {str(e)}")

# 更新文档文件
@router.put("/documents/{document_id}/file")
async def update_document_file(
    document_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    更新文档文件
    """
    logger.info(f"用户 {current_user.id} 请求更新文档 {document_id} 的文件")
    
    # 查找文档
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()
    
    if not document:
        logger.warning(f"文档 {document_id} 不存在或用户 {current_user.id} 无权访问")
        raise HTTPException(status_code=404, detail="文档不存在")
    
    try:
        # 删除旧文件
        if document.stored_path:
            if document.stored_path.startswith("minio://"):
                # MinIO存储
                minio_path = document.stored_path[8:]  # 移除 "minio://" 前缀
                from module.storage_service import delete_file_from_storage
                delete_result = delete_file_from_storage(minio_path=minio_path)
                logger.debug(f"旧MinIO文件删除结果: {delete_result}")
            else:
                # 本地存储
                from module.storage_service import delete_file_from_storage
                delete_result = delete_file_from_storage(file_path=document.stored_path)
                logger.debug(f"旧本地文件删除结果: {delete_result}")
        
        # 保存新文件
        logger.debug(f"保存新文件: {file.filename}")
        storage_result = await save_uploaded_file(file, folder_path="documents")
        
        # 更新文档记录
        document.original_filename = file.filename
        document.stored_path = storage_result.get("local_path")
        
        # 如果是MinIO存储，将MinIO路径存储在额外字段中
        if storage_result.get("minio_path"):
            if not storage_result.get("local_path"):
                document.stored_path = f"minio://{storage_result.get('minio_path')}"
        
        db.commit()
        db.refresh(document)
        
        logger.info(f"用户 {current_user.id} 成功更新文档 {document_id} 的文件")
        return document
    except Exception as e:
        logger.error(f"更新文档文件失败: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新文档文件失败: {str(e)}")

# 提问接口
@router.post("/ask", response_model=AskResponse)
def ask_question(
    request: AskRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # 声明全局变量
    global VECTOR_DIM
    
    logger.info(f"用户 {current_user.id} 提问: {request.question[:50]}{'...' if len(request.question) > 50 else ''}")
    
    try:
        # 检查缓存
        logger.debug(f"检查问题缓存: {request.question[:30]}...")
        cached_answer = get_cached_qa_result(current_user.id, request.question)
        
        if cached_answer:
            logger.info(f"问题命中缓存，直接返回缓存答案")
            return {"answer": cached_answer}
        
        # 获取用户的Milvus集合名称
        collection_name = f"docs_user_{current_user.id}"
        
        from pymilvus import utility
        if not utility.has_collection(collection_name):
            # 如果集合不存在，返回提示信息
            logger.warning(f"用户 {current_user.id} 的Milvus集合 {collection_name} 不存在")
            return {"answer": "您还没有上传任何文档，请先上传文档后再提问。"}
        
        # 生成问题向量
        logger.debug(f"生成问题向量: {request.question[:30]}...")
        try:
            # 从环境变量获取embedding模型配置
            embedding_model_url = EMBEDDING_MODEL_URL or "http://localhost:11434/v1"
            embedding_model_name = EMBEDDING_MODEL_NAME or "nomic-embed-text:latest"
            embedding_api_key = EMBEDDING_MODEL_API_KEY
            
            # 如果客户端指定了模型，则使用指定的模型
            if request.embedding_model_id:
                embedding_model_name = request.embedding_model_id
                
            logger.info(f"使用embedding模型: {embedding_model_name}，URL: {embedding_model_url}")
            
            # 创建嵌入模型配置参数
            embedding_params = {
                "model": embedding_model_name
            }
            
            # 对于Ollama模型，设置base_url和api_key
            if "ollama" in embedding_model_url.lower() or ":" in embedding_model_name:
                # 处理URL格式
                if embedding_model_url.endswith('/v1'):
                    base_url = embedding_model_url
                else:
                    base_url = embedding_model_url.rstrip('/') + '/v1'
                
                # 对于Ollama，使用特定的配置
                embedding_params["base_url"] = base_url
                embedding_params["api_key"] = "None"  # Ollama不需要真实的API密钥
                logger.info(f"配置Ollama embedding模型: {base_url}")
            else:
                # OpenAI模型配置
                if embedding_api_key:
                    embedding_params["api_key"] = embedding_api_key
            
            # 使用新的langchain-openai包
            try:
                from langchain_openai import OpenAIEmbeddings
                embeddings = OpenAIEmbeddings(**embedding_params)
            except ImportError:
                # 如果没有安装langchain-openai，使用旧版本但忽略警告
                import warnings
                warnings.filterwarnings("ignore", category=DeprecationWarning)
                from langchain.embeddings import OpenAIEmbeddings
                # 移除新包特有的参数
                if "base_url" in embedding_params:
                    embedding_params["openai_api_base"] = embedding_params.pop("base_url")
                if "api_key" in embedding_params:
                    embedding_params["openai_api_key"] = embedding_params.pop("api_key")
                embeddings = OpenAIEmbeddings(**embedding_params)
            
            query_vector = embeddings.embed_query(request.question)
            logger.info(f"问题向量生成成功，维度: {len(query_vector)}")
            
            # 检查并确保集合维度匹配
            actual_vector_dim = len(query_vector)
            logger.debug(f"检查Milvus集合 {collection_name} 的维度是否匹配查询向量维度 {actual_vector_dim}")
            
            # 更新全局维度配置
            if VECTOR_DIM != actual_vector_dim:
                VECTOR_DIM = actual_vector_dim
                logger.info(f"更新全局VECTOR_DIM为: {VECTOR_DIM}")
            
            # 确保集合存在且维度匹配
            try:
                from module.milvus_service import create_user_collection
                # 使用实际维度创建或检查集合
                collection_name = create_user_collection(current_user.id, actual_vector_dim)
                logger.info(f"Milvus集合 {collection_name} 维度验证完成")
            except Exception as collection_error:
                logger.error(f"集合维度验证失败: {str(collection_error)}")
                # 如果集合操作失败，返回错误信息
                return {"answer": "文档检索系统配置异常，请联系管理员。"}
        except Exception as e:
            logger.error(f"问题向量生成失败: {str(e)}")
            # 如果向量生成失败，使用占位符向量继续
            query_vector = [0.1] * VECTOR_DIM
        
        # 搜索相似向量
        logger.debug(f"在Milvus集合 {collection_name} 中搜索相似向量")
        results = search_similar_vectors(collection_name, query_vector, limit=5)
        logger.info(f"搜索完成，找到 {len(results[0]) if results else 0} 条相关文档片段")
        
        # 构建上下文
        context = ""
        for hits in results:
            for hit in hits:
                context += f"{hit.entity.get('content')}\n"
        
        # 调用LLM生成答案
        logger.debug(f"调用LLM生成答案，上下文长度: {len(context)} 字符")
        try:
            if context:
                # 根据环境变量选择合适的模型
                chat_model_url = CHAT_MODEL_URL or "http://localhost:11434/v1"
                chat_model_name = CHAT_MODEL_NAME or "qwen3:8b"
                chat_api_key = CHAT_MODEL_API_KEY
                
                logger.info(f"使用聊天模型: {chat_model_name}，URL: {chat_model_url}")
                
                # 创建聊天模型配置参数
                chat_params = {
                    "model": chat_model_name,
                    "temperature": 0.7,
                    "max_tokens": 1000
                }
                
                # 对于Ollama模型，设置base_url和api_key
                if "ollama" in chat_model_url.lower() or ":" in chat_model_name:
                    # 处理URL格式
                    if chat_model_url.endswith('/v1'):
                        base_url = chat_model_url
                    else:
                        base_url = chat_model_url.rstrip('/') + '/v1'
                    
                    chat_params["base_url"] = base_url
                    chat_params["api_key"] = "None"  # Ollama不需要真实的API密钥
                    logger.info(f"配置Ollama聊天模型: {base_url}")
                else:
                    # OpenAI模型配置
                    if chat_api_key:
                        chat_params["api_key"] = chat_api_key
                
                # 使用新的langchain-openai包
                try:
                    from langchain_openai import ChatOpenAI
                    llm = ChatOpenAI(**chat_params)
                except ImportError:
                    # 如果没有安装langchain-openai，使用旧版本但忽略警告
                    import warnings
                    warnings.filterwarnings("ignore", category=DeprecationWarning)
                    from langchain.chat_models import ChatOpenAI
                    # 移除新包特有的参数
                    if "base_url" in chat_params:
                        chat_params["openai_api_base"] = chat_params.pop("base_url")
                    if "api_key" in chat_params:
                        chat_params["openai_api_key"] = chat_params.pop("api_key")
                    llm = ChatOpenAI(**chat_params)
                
                # 构建提示
                prompt = f"基于以下上下文内容，回答用户的问题。\n\n上下文：{context}\n\n问题：{request.question}\n\n回答："
                
                # 使用新的invoke方法替代predict
                try:
                    response = llm.invoke(prompt)
                    if hasattr(response, 'content'):
                        answer = response.content.strip()
                    else:
                        answer = str(response).strip()
                except AttributeError:
                    # 如果invoke方法不可用，使用predict方法
                    response = llm.predict(prompt)
                    answer = response.strip()
            else:
                answer = "没有找到相关内容。"
            
            logger.info(f"答案生成完成，答案长度: {len(answer)} 字符")
        except Exception as e:
            logger.error(f"答案生成失败: {str(e)}")
            answer = "生成答案时发生错误，请稍后重试。"
        
        # 保存到缓存
        logger.debug(f"将问答结果保存到缓存")
        cache_qa_result(current_user.id, request.question, answer)
        
        # 保存到历史记录
        logger.debug(f"将问答记录保存到数据库")
        qa_history = QAHistory(
            user_id=current_user.id,
            question=request.question,
            answer=answer,
        )
        db.add(qa_history)
        db.commit()
        logger.info(f"问答历史记录保存成功，记录ID: {qa_history.id}")
        
        return {"answer": answer}
    except Exception as e:
        logger.error(f"问答处理失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"问答处理失败: {str(e)}")

# 获取问答历史
@router.get("/history")
def get_qa_history(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    获取用户的问答历史记录
    """
    logger.info(f"用户 {current_user.id} 请求获取问答历史记录")
    
    try:
        # 查询用户的问答历史记录
        qa_history = db.query(QAHistory).filter(
            QAHistory.user_id == current_user.id
        ).order_by(QAHistory.created_at.desc()).all()
        
        logger.info(f"成功获取用户 {current_user.id} 的问答历史记录，共 {len(qa_history)} 条")
        return qa_history
    except Exception as e:
        logger.error(f"获取问答历史记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取问答历史记录失败: {str(e)}")

# 删除文档
@router.delete("/documents/{document_id}")
def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    logger.info(f"用户 {current_user.id} 请求删除文档 {document_id}")
    
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()
    
    if not document:
        logger.warning(f"文档 {document_id} 不存在或用户 {current_user.id} 无权访问")
        raise HTTPException(status_code=404, detail="文档不存在")
    
    try:
        # 删除存储的文件
        if document.stored_path:
            if document.stored_path.startswith("minio://"):
                # MinIO存储
                minio_path = document.stored_path[8:]  # 移除 "minio://" 前缀
                from module.storage_service import delete_file_from_storage
                delete_result = delete_file_from_storage(minio_path=minio_path)
                logger.debug(f"MinIO文件删除结果: {delete_result}")
            else:
                # 本地存储
                from module.storage_service import delete_file_from_storage
                delete_result = delete_file_from_storage(file_path=document.stored_path)
                logger.debug(f"本地文件删除结果: {delete_result}")
        
        # 删除数据库记录
        db.delete(document)
        db.commit()
        
        logger.info(f"用户 {current_user.id} 成功删除文档 {document_id}")
        return {"message": "文档已成功删除"}
    except Exception as e:
        logger.error(f"删除文档失败: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除文档失败: {str(e)}")