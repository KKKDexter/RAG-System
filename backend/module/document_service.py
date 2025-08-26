import os
import tempfile
from typing import List, Tuple, Optional
from fastapi import HTTPException

# 导入文档加载器
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    Docx2txtLoader
)

# 导入文本分割器
from langchain.text_splitter import RecursiveCharacterTextSplitter

# 导入嵌入模型 - 使用新的导入方式
from langchain_openai import OpenAIEmbeddings

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
def process_document(file_path: str = None, minio_path: str = None, file_extension: str = None, embedding_model_name: str = None) -> Tuple[List, OpenAIEmbeddings]:
    """
    处理文档，支持从本地或MinIO读取文件
    
    Args:
        file_path: 本地文件路径
        minio_path: MinIO文件路径
        file_extension: 文件扩展名
        embedding_model_name: 指定的embedding模型名称
    
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
    model_name = embedding_model_name or EMBEDDING_MODEL_NAME
    logger.debug(f"创建嵌入模型: {model_name}")
    try:
        # 先尝试从数据库获取模型配置
        api_key = EMBEDDING_MODEL_API_KEY
        model_url = None
        
        # 尝试从数据库获取模型
        try:
            from sqlalchemy import create_engine
            # 直接使用engine而不是导入get_db_engine
            from .database import engine
            from .models import LLMModel
            from sqlalchemy.orm import sessionmaker
            
            # 创建临时数据库会话
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            db = SessionLocal()
            
            try:
                # 根据模型名称查询
                if model_name:
                    db_model = db.query(LLMModel).filter(
                        LLMModel.name == model_name,
                        LLMModel.type == "embedding",
                        LLMModel.is_active == True,
                        LLMModel.is_delete == False
                    ).first()
                    
                    if db_model:
                        logger.info(f"从数据库获取到模型配置: {model_name}")
                        api_key = db_model.api_key or api_key
                        model_url = db_model.base_url
                    else:
                        logger.info(f"数据库中未找到模型 {model_name}，使用默认配置")
            finally:
                db.close()
                
        except Exception as db_error:
            logger.warning(f"从数据库获取模型配置失败: {str(db_error)}")
        
        # 创建嵌入模型配置参数
        embedding_params = {
            "request_timeout": 30,  # 30秒超时
            "max_retries": 3,       # 最大重试次数
        }
        
        # 如果设置了API Key，则添加
        if api_key:
            embedding_params["api_key"] = api_key
        else:
            logger.warning("未配置EMBEDDING_MODEL_API_KEY，将使用环境变量OPENAI_API_KEY")
        
        # 如果设置了模型名称，则添加
        if model_name:
            embedding_params["model"] = model_name
            
        # 如果设置了基础URL，则添加
        if model_url:
            embedding_params["base_url"] = model_url
            logger.info(f"使用自定义基础URL: {model_url}")
            
        # 创建嵌入模型实例（根据模型名称选择不同的嵌入类）
        is_ollama_model = (
            "nomic" in model_name.lower() or 
            "embed" in model_name.lower() or 
            ":" in model_name or 
            "localhost" in str(model_url) or 
            "192.168.1.11" in str(model_url) or
            model_url and "11434" in str(model_url)  # Ollama默认端口
        )
        
        if is_ollama_model:
            # 这是Ollama本地模型
            try:
                from langchain_community.embeddings import OllamaEmbeddings
                logger.info(f"使用Ollama嵌入模型: {model_name}, 服务地址: {model_url}")
                
                # Ollama模型参数
                ollama_params = {
                    "model": model_name,
                }
                
                # 处理不同的URL格式
                if model_url:
                    if model_url.endswith('/v1'):
                        # 如果是/v1结尾，去掉/v1部分
                        base_url = model_url.replace('/v1', '')
                    else:
                        base_url = model_url
                    ollama_params["base_url"] = base_url
                    logger.info(f"Ollama基础URL: {base_url}")
                else:
                    ollama_params["base_url"] = "http://localhost:11434"  # Ollama默认端口
                
                embeddings = OllamaEmbeddings(**ollama_params)
                logger.info(f"Ollama嵌入模型创建成功: {model_name}")
                
            except ImportError as import_error:
                logger.error(f"Ollama依赖不可用: {import_error}")
                logger.error("请安装: pip install langchain-community")
                raise HTTPException(
                    status_code=500, 
                    detail=f"Ollama依赖缺失: {str(import_error)}"
                )
            except Exception as ollama_error:
                logger.error(f"Ollama模型初始化失败: {str(ollama_error)}")
                raise HTTPException(
                    status_code=500, 
                    detail=f"Ollama模型初始化失败: {str(ollama_error)}"
                )
        else:
            # 使用OpenAI模型
            logger.info(f"使用OpenAI嵌入模型: {model_name}")
            embeddings = OpenAIEmbeddings(**embedding_params)
        
        # 测试模型是否可用（用一个简单的测试文本）
        # 在函数开始处声明global
        global VECTOR_DIM
        
        try:
            test_embedding = embeddings.embed_query("测试文本")
            actual_dim = len(test_embedding)
            
            # 对于Ollama模型，向量维度可能不同于默认的OpenAI维度
            if ("nomic" in model_name.lower() or 
                "ollama" in str(type(embeddings)).lower() or
                "192.168.1.11" in str(model_url)):
                logger.info(f"Ollama嵌入模型测试成功: {model_name}, 向量维度: {actual_dim}")
                # 更新VECTOR_DIM为实际维度，以便后续使用
                VECTOR_DIM = actual_dim
                logger.info(f"更新VECTOR_DIM为: {VECTOR_DIM}")
            elif actual_dim != VECTOR_DIM:
                logger.warning(f"向量维度不匹配: 期望 {VECTOR_DIM}，实际 {actual_dim}")
            else:
                logger.info(f"嵌入模型测试成功: {model_name}, 向量维度: {actual_dim}")
                
        except Exception as test_error:
            logger.error(f"嵌入模型测试失败: {str(test_error)}")
            # 对于Ollama模型，如果测试失败，不抛出异常，让后续代码尝试处理
            if ("nomic" in model_name.lower() or 
                "192.168.1.11" in str(model_url) or
                "localhost" in str(model_url)):
                logger.warning(f"Ollama模型测试失败，但继续处理: {str(test_error)}")
                # 对于Ollama模型，使用默认维度或推测维度
                if "nomic" in model_name.lower():
                    VECTOR_DIM = 768  # nomic-embed-text的常见维度
                    logger.info(f"使用Ollama模型默认维度: {VECTOR_DIM}")
            else:
                # 对于非Ollama模型，记录警告但不抛出异常
                logger.warning(f"OpenAI模型测试失败，但继续处理: {str(test_error)}")
            
        logger.info(f"嵌入模型创建成功: {model_name}")
        
    except Exception as e:
        logger.error(f"嵌入模型创建失败: {str(e)}")
        # 提供更详细的错误信息
        error_details = [
            f"模型名称: {model_name}",
            f"API Key 状态: {'已配置' if api_key else '未配置'}",
            f"基础URL: {model_url or '默认'}",
            f"原始错误: {str(e)}"
        ]
        raise HTTPException(
            status_code=500, 
            detail=f"嵌入模型初始化失败: {'; '.join(error_details)}"
        )
    
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

