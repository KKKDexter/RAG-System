import os
from typing import List, Optional
from pymilvus import connections, Collection, CollectionSchema, FieldSchema, DataType, utility

# 导入日志配置
from logger_config import get_logger
logger = get_logger("milvus_service")

# 根据环境动态获取配置
current_env = os.getenv('ENVIRONMENT', 'dev')
try:
    env_config = __import__(f"config.{current_env}", fromlist=["*"])
    MILVUS_HOST = env_config.MILVUS_HOST
    MILVUS_PORT = env_config.MILVUS_PORT
    VECTOR_DIM = env_config.VECTOR_DIM
    MILVUS_USERNAME = getattr(env_config, 'MILVUS_USERNAME', None)
    MILVUS_PASSWORD = getattr(env_config, 'MILVUS_PASSWORD', None)
except Exception as e:
    logger.error(f"加载配置失败: {e}，使用默认配置")
    MILVUS_HOST = "localhost"
    MILVUS_PORT = 19530
    VECTOR_DIM = 1536
    MILVUS_USERNAME = None
    MILVUS_PASSWORD = None

def connect_to_milvus(max_retries: int = 3) -> bool:
    """
    连接到Milvus服务器，带有重试机制
    
    Args:
        max_retries (int): 最大重试次数
    
    Returns:
        bool: 连接是否成功
    """
    logger.info(f"尝试连接Milvus服务器: {MILVUS_HOST}:{MILVUS_PORT}")
    
    for attempt in range(max_retries):
        try:
            # 创建连接参数
            conn_params = {
                "host": MILVUS_HOST,
                "port": MILVUS_PORT
            }
            
            # 如果设置了用户名和密码，则添加认证
            if MILVUS_USERNAME and MILVUS_PASSWORD:
                conn_params["user"] = MILVUS_USERNAME
                conn_params["password"] = MILVUS_PASSWORD
                logger.debug("Milvus连接包含用户名和密码认证")
            
            connections.connect("default", **conn_params)
            logger.info("Milvus服务器连接成功")
            return True
            
        except Exception as e:
            logger.warning(f"Milvus连接尝试 {attempt + 1}/{max_retries} 失败: {str(e)}")
            if attempt == max_retries - 1:
                logger.error(f"Milvus服务器连接失败，所有重试都已用尽: {str(e)}")
                raise
            else:
                import time
                time.sleep(2 ** attempt)  # 指数退避
    
    return False

# 创建用户集合（支持动态向量维度）
def create_user_collection(user_id: int, vector_dim: int = None) -> str:
    collection_name = f"docs_user_{user_id}"
    actual_dim = vector_dim or VECTOR_DIM
    logger.info(f"为用户 {user_id} 创建/检查Milvus集合: {collection_name}，向量维度: {actual_dim}")
    
    try:
        # 检查集合是否已存在
        if utility.has_collection(collection_name):
            # 检查现有集合的维度是否匹配
            existing_collection = Collection(name=collection_name)
            existing_schema = existing_collection.schema
            
            # 查找向量字段的维度
            vector_field = None
            for field in existing_schema.fields:
                if field.name == "vector":
                    vector_field = field
                    break
            
            if vector_field and hasattr(vector_field, 'params'):
                existing_dim = vector_field.params.get('dim', VECTOR_DIM)
                if existing_dim != actual_dim:
                    logger.warning(f"集合 {collection_name} 存在但维度不匹配（期望 {actual_dim}，实际 {existing_dim}），将删除并重建")
                    # 删除现有集合
                    utility.drop_collection(collection_name)
                    logger.info(f"已删除维度不匹配的集合: {collection_name}")
                else:
                    logger.info(f"集合 {collection_name} 已存在且维度匹配，直接返回")
                    return collection_name
            else:
                logger.warning(f"无法获取集合 {collection_name} 的向量维度信息，假设匹配")
                return collection_name
        
        # 创建集合
        logger.debug(f"开始创建集合: {collection_name}，向量维度: {actual_dim}")
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="document_id", dtype=DataType.INT64),
            FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=actual_dim),
        ]
        
        schema = CollectionSchema(fields, description=f"User {user_id} documents collection (dim={actual_dim})")
        collection = Collection(name=collection_name, schema=schema)
        logger.info(f"集合 {collection_name} 创建成功，向量维度: {actual_dim}")
        
        # 创建索引
        logger.debug(f"为集合 {collection_name} 创建向量索引")
        index_params = {
            "index_type": "IVF_FLAT",
            "metric_type": "L2",
            "params": {"nlist": 128}
        }
        collection.create_index(field_name="vector", index_params=index_params)
        logger.info(f"集合 {collection_name} 索引创建成功")
        
        return collection_name
    except Exception as e:
        logger.error(f"创建集合 {collection_name} 失败: {str(e)}")
        raise

# 搜索相似向量
# 获取或创建Milvus集合
def get_milvus_collection(collection_name: str) -> Collection:
    """
    获取或创建Milvus集合
    
    Args:
        collection_name (str): 集合名称
    
    Returns:
        Collection: Milvus集合对象
    """
    logger.info(f"获取Milvus集合: {collection_name}")
    
    try:
        if not utility.has_collection(collection_name):
            # 如果集合不存在，创建一个新的（与create_user_collection保持一致）
            logger.debug(f"集合 {collection_name} 不存在，创建新集合")
            fields = [
                FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
                FieldSchema(name="document_id", dtype=DataType.INT64),  # 修复：使用INT64类型保持一致
                FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
                FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=VECTOR_DIM),
            ]
            
            schema = CollectionSchema(fields, description=f"Collection for {collection_name}")
            collection = Collection(name=collection_name, schema=schema)
            
            # 创建索引
            index_params = {
                "index_type": "IVF_FLAT",
                "metric_type": "L2",
                "params": {"nlist": 128}
            }
            collection.create_index(field_name="vector", index_params=index_params)
            logger.info(f"集合 {collection_name} 创建成功")
        else:
            collection = Collection(name=collection_name)
            logger.debug(f"集合 {collection_name} 已存在")
        
        return collection
    except Exception as e:
        logger.error(f"获取集合 {collection_name} 失败: {str(e)}")
        raise

# 删除Milvus集合
def drop_collection(collection_name: str) -> bool:
    """
    删除Milvus集合
    
    Args:
        collection_name (str): 集合名称
    
    Returns:
        bool: 是否删除成功
    """
    logger.info(f"删除Milvus集合: {collection_name}")
    
    try:
        if utility.has_collection(collection_name):
            utility.drop_collection(collection_name)
            logger.info(f"集合 {collection_name} 删除成功")
            return True
        else:
            logger.warning(f"集合 {collection_name} 不存在，无需删除")
            return False
    except Exception as e:
        logger.error(f"删除集合 {collection_name} 失败: {str(e)}")
        raise

# 搜索相似向量
def search_similar_vectors(collection_name: str, query_vector: list, limit: int = 5) -> list:
    logger.info(f"在Milvus集合 {collection_name} 中搜索相似向量，限制结果数: {limit}")
    
    try:
        if not utility.has_collection(collection_name):
            logger.warning(f"集合 {collection_name} 不存在，返回空结果")
            return []
        
        logger.debug(f"加载集合 {collection_name}")
        collection = Collection(name=collection_name)
        collection.load()
        logger.info(f"集合 {collection_name} 加载成功")
        
        logger.debug(f"设置搜索参数，执行相似向量搜索")
        search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
        results = collection.search(
            data=[query_vector],
            anns_field="vector",
            param=search_params,
            limit=limit,
            output_fields=["content"]
        )
        
        logger.info(f"相似向量搜索完成，找到 {len(results[0]) if results else 0} 个匹配结果")
        return results
    except Exception as e:
        logger.error(f"相似向量搜索失败: {str(e)}")
        raise