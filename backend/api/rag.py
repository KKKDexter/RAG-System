import os
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from module.database import get_db
from module.models import Document, User, QAHistory
from module.schemas import DocumentOut, AskRequest, AskResponse, UserOut
from module.auth import get_current_active_user, is_admin
from module.milvus_service import search_similar_vectors
from module.document_service import process_document, create_upload_dir, save_uploaded_file
from module.redis_service import cache_qa_result, get_cached_qa_result
# 根据环境变量动态导入配置
env = os.environ.get('ENVIRONMENT', 'dev')
if env == 'prod':
    from config.prod import VECTOR_DIM, EMBEDDING_MODEL_API_KEY, EMBEDDING_MODEL_NAME, CHAT_MODEL_API_KEY, CHAT_MODEL_NAME, CHAT_MODEL_URL, RERANK_MODEL_API_KEY, RERANK_MODEL_NAME, RERANK_MODEL_URL
else:
    from config.dev import VECTOR_DIM, EMBEDDING_MODEL_API_KEY, EMBEDDING_MODEL_NAME, CHAT_MODEL_API_KEY, CHAT_MODEL_NAME, CHAT_MODEL_URL, RERANK_MODEL_API_KEY, RERANK_MODEL_NAME, RERANK_MODEL_URL
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

# 上传文档
@router.post("/upload", response_model=DocumentOut)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    logger.info(f"用户 {current_user.id} 上传文档: {file.filename}")
    
    # 创建上传目录
    upload_dir = create_upload_dir()
    
    try:
        # 保存文件
        logger.debug(f"保存上传文件: {file.filename}")
        file_path, file_extension = await save_uploaded_file(file, upload_dir)
        
        # 创建文档记录
        logger.debug(f"创建文档数据库记录: {file.filename}")
        document = Document(
            user_id=current_user.id,
            original_filename=file.filename,
            stored_path=file_path,
            milvus_collection_name=f"docs_user_{current_user.id}",
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        logger.info(f"文档记录创建成功，文档ID: {document.id}")
        
        # 处理文档
        logger.debug(f"处理文档: {file.filename}，文档ID: {document.id}")
        texts, embeddings = process_document(file_path, file_extension)
        
        # 获取用户的Milvus集合
        logger.debug(f"加载Milvus集合: {document.milvus_collection_name}")
        from pymilvus import Collection
        from module.milvus_service import create_user_collection
        # 确保集合存在
        collection_name = create_user_collection(current_user.id)
        collection = Collection(name=collection_name)
        collection.load()
        
        # 准备数据
        logger.debug(f"为文档 {document.id} 准备向量数据")
        vectors = []
        contents = []
        document_ids = []
        
        for text in texts:
            # 生成向量 (这里使用占位符向量)
            vector = [0.1] * VECTOR_DIM  # 实际应该使用embeddings.embed_documents()
            vectors.append(vector)
            contents.append(text.page_content)
            document_ids.append(document.id)
        
        # 插入数据
        logger.debug(f"向Milvus集合中插入 {len(vectors)} 条向量数据")
        collection.insert([document_ids, contents, vectors])
        collection.flush()
        logger.info(f"文档向量数据插入成功，文档ID: {document.id}")
        
        return document
    except Exception as e:
        # 删除已保存的文件和文档记录
        logger.error(f"文档上传处理失败: {str(e)}")
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        if 'document' in locals():
            db.delete(document)
            db.commit()
        raise HTTPException(status_code=500, detail=f"文档处理失败: {str(e)}")

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
            # 创建嵌入模型配置参数
            embedding_params = {}
            
            # 如果设置了API Key，则添加
            if EMBEDDING_MODEL_API_KEY:
                embedding_params["openai_api_key"] = EMBEDDING_MODEL_API_KEY
            
            # 如果设置了模型名称，则添加
            if EMBEDDING_MODEL_NAME:
                embedding_params["model"] = EMBEDDING_MODEL_NAME
            
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