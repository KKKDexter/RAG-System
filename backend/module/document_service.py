import os
import uuid
import asyncio
from typing import Tuple, List, Optional
from fastapi import HTTPException
# 修复弃用的导入路径
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.chat_models import ChatOpenAI

# 导入统一存储服务
from module.storage_service import save_file_to_storage, get_file_from_storage

# 根据环境变量动态导入配置
env = os.environ.get('ENVIRONMENT', 'dev')
if env == 'prod':
    from config.prod import CHUNK_SIZE, CHUNK_OVERLAP, VECTOR_DIM, EMBEDDING_MODEL_API_KEY, EMBEDDING_MODEL_NAME
else:
    from config.dev import CHUNK_SIZE, CHUNK_OVERLAP, VECTOR_DIM, EMBEDDING_MODEL_API_KEY, EMBEDDING_MODEL_NAME

# 导入日志配置
from logger_config import get_logger
logger = get_logger("document_service")

# 处理文档
def process_document(file_path: str = None, minio_path: str = None, file_extension: str = None) -> Tuple[List, OpenAIEmbeddings]:
    """
    处理文档，支持从本地或MinIO读取文件
    
    Args:
        file_path: 本地文件路径
        minio_path: MinIO文件路径
        file_extension: 文件扩展名
    
    Returns:
        Tuple[List, OpenAIEmbeddings]: 文本块列表和嵌入模型
    """
    # 确定文件扩展名
    if not file_extension:
        if file_path:
            file_extension = os.path.splitext(file_path)[1].lower()
        elif minio_path:
            file_extension = os.path.splitext(minio_path)[1].lower()
        else:
            raise ValueError("必须提供文件路径或文件扩展名")
    
    display_name = file_path or minio_path or "unknown_file"
    logger.info(f"开始处理文档: {os.path.basename(display_name)}, 格式: {file_extension}")
    
    # 获取文件内容用于加载
    temp_file_path = None
    try:
        if file_path and os.path.exists(file_path):
            # 使用本地文件
            temp_file_path = file_path
            logger.debug(f"使用本地文件: {file_path}")
        elif minio_path:
            # 从 MinIO 下载文件到临时目录
            import tempfile
            file_stream = get_file_from_storage(minio_path=minio_path)
            
            # 创建临时文件
            temp_fd, temp_file_path = tempfile.mkstemp(suffix=file_extension)
            try:
                with os.fdopen(temp_fd, 'wb') as temp_file:
                    temp_file.write(file_stream.read())
            finally:
                file_stream.close()
            
            logger.debug(f"从 MinIO 下载文件到临时路径: {temp_file_path}")
        else:
            raise ValueError("无法获取文件内容，本地文件不存在且未提供MinIO路径")
    
        # 根据文件扩展名选择合适的加载器
        if file_extension == ".pdf":
            logger.debug(f"使用PDF加载器处理文件: {temp_file_path}")
            loader = PyPDFLoader(temp_file_path)
        elif file_extension == ".txt":
            logger.debug(f"使用文本加载器处理文件: {temp_file_path}")
            loader = TextLoader(temp_file_path, encoding="utf-8")
        elif file_extension in [".docx", ".doc"]:
            logger.debug(f"使用DOCX加载器处理文件: {temp_file_path}")
            loader = Docx2txtLoader(temp_file_path)
        else:
            logger.error(f"不支持的文件格式: {file_extension}")
            raise ValueError(f"不支持的文件格式: {file_extension}")
        # 加载文档
        logger.debug(f"开始加载文档: {temp_file_path}")
        try:
            documents = loader.load()
            logger.info(f"文档加载成功，共 {len(documents)} 页")
        except Exception as e:
            logger.error(f"文档加载失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"文档加载失败: {str(e)}")
        
    finally:
        # 清理临时文件（只清理从 MinIO 下载的临时文件）
        if temp_file_path and temp_file_path != file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
                logger.debug(f"清理临时文件: {temp_file_path}")
            except Exception as e:
                logger.warning(f"清理临时文件失败: {str(e)}")
    
    # 分割文本
    logger.debug(f"开始分割文本，块大小: {CHUNK_SIZE}, 重叠: {CHUNK_OVERLAP}")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
    )
    
    try:
        texts = text_splitter.split_documents(documents)
        logger.info(f"文本分割成功，生成 {len(texts)} 个文本块")
    except Exception as e:
        logger.error(f"文本分割失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文本分割失败: {str(e)}")
    
    # 生成向量 (使用配置的嵌入模型参数)
    logger.debug(f"创建嵌入模型: {EMBEDDING_MODEL_NAME}")
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
        logger.info(f"嵌入模型创建成功: {EMBEDDING_MODEL_NAME}")
    except Exception as e:
        logger.error(f"嵌入模型创建失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"嵌入模型初始化失败: {str(e)}")
    
    return texts, embeddings

# 获取存储目录（不自动创建）
def get_storage_dir(folder_path: str = "documents") -> str:
    """
    获取存储目录路径，不自动创建目录
    
    Args:
        folder_path: 文件夹路径
        
    Returns:
        str: 存储目录路径
    """
    logger.debug(f"获取存储目录路径: {folder_path}")
    storage_dir = os.path.join(os.getcwd(), folder_path)
    logger.info(f"存储目录路径: {storage_dir}")
    return storage_dir

# 保存上传文件（使用统一存储服务）
async def save_uploaded_file(file, storage_type: Optional[str] = None, folder_path: str = "documents") -> dict:
    """
    保存上传文件到指定存储
    
    Args:
        file: 上传的文件对象
        storage_type: 存储类型 (local, minio, both)
        folder_path: 文件夹路径
    
    Returns:
        dict: 存储结果信息
    """
    logger.info(f"开始保存上传文件: {file.filename}，存储类型: {storage_type}")
    
    try:
        result = await save_file_to_storage(file, folder_path, storage_type)
        logger.info(f"文件保存成功: {file.filename}")
        return result
    except Exception as e:
        logger.error(f"文件保存失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")