import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from module.database import get_db
from module.models import Document, User, QAHistory
from module.schemas import DocumentOut, AskRequest, AskResponse
from module.auth_service import get_current_active_user
from module.milvus_service import search_similar_vectors
from module.document_service import process_document, save_uploaded_file, get_storage_dir
from module.storage_service import get_storage_service_info
from module.redis_service import cache_qa_result, get_cached_qa_result
import asyncio  # 添加asyncio导入

# 根据环境变量动态导入配置
env = os.environ.get('ENVIRONMENT', 'dev')
if env == 'prod':
    from config.prod import VECTOR_DIM, EMBEDDING_MODEL_API_KEY, EMBEDDING_MODEL_NAME, CHAT_MODEL_API_KEY, CHAT_MODEL_NAME, CHAT_MODEL_URL
else:
    from config.dev import VECTOR_DIM, EMBEDDING_MODEL_API_KEY, EMBEDDING_MODEL_NAME, CHAT_MODEL_API_KEY, CHAT_MODEL_NAME, CHAT_MODEL_URL

from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.chat_models import ChatOpenAI

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
        db_session: 数据库会话
    """
    try:
        logger.info(f"开始异步处理文档 ID: {document_id}")
        
        # 查询文档
        document = db_session.query(Document).filter(Document.id == document_id).first()
        if not document:
            logger.error(f"找不到文档 ID: {document_id}")
            return
        
        # 处理文档
        if storage_result.get("local_path"):
            # 从本地路径处理
            texts, embeddings = process_document(
                file_path=storage_result["local_path"], 
                file_extension=storage_result["file_extension"],
                embedding_model_name=embedding_model_id  # 传递embedding模型名称
            )
        elif storage_result.get("minio_path"):
            # 从MinIO路径处理
            texts, embeddings = process_document(
                minio_path=storage_result["minio_path"], 
                file_extension=storage_result["file_extension"],
                embedding_model_name=embedding_model_id  # 传递embedding模型名称
            )
        else:
            logger.error(f"文档 {document_id} 没有有效的存储路径")
            return
        
        # 获取用户的Milvus集合
        logger.debug(f"加载Milvus集合: {document.milvus_collection_name}")
        from pymilvus import Collection
        from module.milvus_service import create_user_collection
        # 确保集合存在
        collection_name = create_user_collection(user_id)
        collection = Collection(name=collection_name)
        collection.load()
        
        # 准备数据
        logger.debug(f"为文档 {document_id} 准备向量数据")
        vectors = []
        contents = []
        document_ids = []
        
        for text in texts:
            # 尝试生成实际向量，失败时使用占位符
            try:
                # 为嵌入查询设置超时时间
                import asyncio
                import functools
                
                # 创建带超时的嵌入查询函数
                async def embed_with_timeout():
                    loop = asyncio.get_event_loop()
                    return await loop.run_in_executor(
                        None, 
                        functools.partial(embeddings.embed_query, text.page_content)
                    )
                
                # 执行带超时的嵌入查询（设置30秒超时）
                try:
                    vector = asyncio.wait_for(embed_with_timeout(), timeout=30.0)
                    if asyncio.iscoroutine(vector):
                        vector = await vector
                    logger.debug(f"成功为文本生成向量，维度: {len(vector)}")
                except asyncio.TimeoutError:
                    logger.error(f"向量生成超时，使用占位符向量")
                    vector = [0.1] * VECTOR_DIM  # 超时时使用占位符向量
            except Exception as e:
                logger.error(f"向量生成失败，使用占位符向量: {str(e)}")
                vector = [0.1] * VECTOR_DIM  # 失败时使用占位符向量
                
            vectors.append(vector)
            contents.append(text.page_content)
            document_ids.append(document_id)
        
        # 插入数据
        logger.debug(f"向Milvus集合中插入 {len(vectors)} 条向量数据")
        collection.insert([document_ids, contents, vectors])
        collection.flush()
        
        # 更新文档状态为已处理
        document.status = "processed"  # 假设Document模型有status字段
        db_session.commit()
        
        logger.info(f"文档 {document_id} 异步处理完成")
    except Exception as e:
        logger.error(f"异步处理文档 {document_id} 失败: {str(e)}")
        try:
            # 更新文档状态为处理失败
            document = db_session.query(Document).filter(Document.id == document_id).first()
            if document:
                document.status = "failed"  # 假设Document模型有status字段
                document.error_message = str(e)[:255]  # 假设Document模型有error_message字段
                db_session.commit()
        except Exception as update_error:
            logger.error(f"更新文档状态失败: {str(update_error)}")

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
                from module.storage_service import delete_file_from_storage
                delete_file_from_storage(
                    storage_result.get("local_path"),
                    storage_result.get("minio_path")
                )
            except Exception as cleanup_error:
                logger.error(f"清理存储文件失败: {str(cleanup_error)}")
        
        if 'document' in locals():
            db.delete(document)
            db.commit()
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
            # 先尝试从数据库获取embedding模型配置
            api_key = EMBEDDING_MODEL_API_KEY
            model_name = EMBEDDING_MODEL_NAME
            model_url = None
            
            # 如果客户端指定了模型，则使用指定的模型
            if request.embedding_model_id:
                model_name = request.embedding_model_id
                
            # 尝试从数据库获取模型配置
            try:
                from module.llm_service import LLMService
                db_model = LLMService.get_llm_model_by_name(db, model_name)
                if db_model and db_model.type == "embedding" and db_model.is_active:
                    logger.info(f"从数据库获取到embedding模型配置: {model_name}")
                    api_key = db_model.api_key
                    model_url = db_model.base_url
            except Exception as db_error:
                logger.warning(f"从数据库获取embedding模型配置失败: {str(db_error)}")
            
            # 创建嵌入模型配置参数
            embedding_params = {}
            
            # 如果设置了API Key，则添加
            if api_key:
                embedding_params["openai_api_key"] = api_key
            
            # 如果设置了模型名称，则添加
            if model_name:
                embedding_params["model"] = model_name
                
            # 如果设置了基础URL，则添加
            if model_url:
                embedding_params["openai_api_base"] = model_url
            
            embeddings = OpenAIEmbeddings(**embedding_params)
            query_vector = embeddings.embed_query(request.question)
            logger.info("问题向量生成成功")
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
                # 创建聊天模型配置参数
                chat_params = {}
                
                # 如果设置了API Key，则添加
                if CHAT_MODEL_API_KEY:
                    chat_params["openai_api_key"] = CHAT_MODEL_API_KEY
                
                # 如果设置了模型名称，则添加
                if CHAT_MODEL_NAME:
                    chat_params["model"] = CHAT_MODEL_NAME
                
                llm = ChatOpenAI(**chat_params)
                
                # 构建提示
                prompt = f"基于以下上下文内容，回答用户的问题。\n\n上下文：{context}\n\n问题：{request.question}\n\n回答："
                
                # 调用LLM生成答案
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