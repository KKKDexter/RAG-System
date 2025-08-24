import os
import uuid
import asyncio
from typing import Tuple, List
from fastapi import HTTPException
# 修复弃用的导入路径
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.chat_models import ChatOpenAI

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
def process_document(file_path: str, file_extension: str) -> Tuple[List, OpenAIEmbeddings]:
    logger.info(f"开始处理文档: {os.path.basename(file_path)}, 格式: {file_extension}")
    
    # 根据文件扩展名选择合适的加载器
    if file_extension == ".pdf":
        logger.debug(f"使用PDF加载器处理文件: {file_path}")
        loader = PyPDFLoader(file_path)
    elif file_extension == ".txt":
        logger.debug(f"使用文本加载器处理文件: {file_path}")
        loader = TextLoader(file_path, encoding="utf-8")
    elif file_extension in [".docx", ".doc"]:
        logger.debug(f"使用DOCX加载器处理文件: {file_path}")
        loader = Docx2txtLoader(file_path)
    else:
        logger.error(f"不支持的文件格式: {file_extension}")
        raise ValueError(f"不支持的文件格式: {file_extension}")
    
    # 加载文档
    logger.debug(f"开始加载文档: {file_path}")
    try:
        documents = loader.load()
        logger.info(f"文档加载成功，共 {len(documents)} 页")
    except Exception as e:
        logger.error(f"文档加载失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文档加载失败: {str(e)}")
    
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

# 创建上传目录
def create_upload_dir() -> str:
    logger.debug("开始创建上传目录")
    upload_dir = os.path.join(os.getcwd(), "uploads")
    try:
        os.makedirs(upload_dir, exist_ok=True)
        logger.info(f"上传目录创建成功: {upload_dir}")
    except Exception as e:
        logger.error(f"上传目录创建失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"上传目录创建失败: {str(e)}")
    return upload_dir

# 保存上传文件
async def save_uploaded_file(file, upload_dir: str) -> Tuple[str, str]:
    original_filename = file.filename
    logger.info(f"开始保存上传文件: {original_filename}")
    
    file_extension = os.path.splitext(original_filename)[1].lower()
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(upload_dir, unique_filename)
    
    logger.debug(f"生成唯一文件名: {unique_filename}，保存路径: {file_path}")
    
    try:
        # 检查是否是异步文件对象 (FastAPI UploadFile)
        if hasattr(file, 'read'):
            # 处理FastAPI UploadFile对象
            if asyncio.iscoroutinefunction(file.read):
                # 异步读取文件内容
                content = await file.read()
            else:
                # 同步读取文件内容
                content = file.read()
            
            with open(file_path, "wb") as buffer:
                buffer.write(content)
        else:
            # 处理其他类型的文件对象
            raise ValueError("不支持的文件对象类型")
        
        logger.info(f"文件保存成功，大小: {len(content)} 字节")
    except Exception as e:
        logger.error(f"文件保存失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")
    
    return file_path, file_extension