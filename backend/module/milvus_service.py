import os
from pymilvus import connections, Collection, CollectionSchema, FieldSchema, DataType, utility

# 根据环境动态获取配置
current_env = os.getenv('ENVIRONMENT', 'dev')
env_config = __import__(f"config.{current_env}", fromlist=["*"])
MILVUS_HOST = env_config.MILVUS_HOST
MILVUS_PORT = env_config.MILVUS_PORT
VECTOR_DIM = env_config.VECTOR_DIM
MILVUS_USERNAME = env_config.MILVUS_USERNAME
MILVUS_PASSWORD = env_config.MILVUS_PASSWORD

# 导入日志配置
from logger_config import get_logger
logger = get_logger("milvus_service")

# 连接Milvus
def connect_to_milvus():
    logger.info(f"尝试连接Milvus服务器: {MILVUS_HOST}:{MILVUS_PORT}")
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
    except Exception as e:
        logger.error(f"Milvus服务器连接失败: {str(e)}")
        raise

# 创建用户集合
def create_user_collection(user_id: int) -> str:
    collection_name = f"docs_user_{user_id}"
    logger.info(f"为用户 {user_id} 创建/检查Milvus集合: {collection_name}")
    
    try:
        # 检查集合是否已存在
        if utility.has_collection(collection_name):
            logger.warning(f"集合 {collection_name} 已存在，直接返回")
            return collection_name
        
        # 创建集合
        logger.debug(f"开始创建集合: {collection_name}")
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="document_id", dtype=DataType.INT64),
            FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=VECTOR_DIM),
        ]
        
        schema = CollectionSchema(fields, description=f"User {user_id} documents collection")
        collection = Collection(name=collection_name, schema=schema)
        logger.info(f"集合 {collection_name} 创建成功")
        
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