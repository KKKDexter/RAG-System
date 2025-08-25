# 生产环境配置

# 安全配置
import os
SECRET_KEY = os.environ.get("SECRET_KEY", "your-secure-production-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 生产环境token有效期更长

# 数据库配置
DATABASE_URL = os.environ.get("DATABASE_URL", "mysql+pymysql://production_user:production_password@db-host/rag_system_prod")

# Milvus配置
MILVUS_HOST = os.environ.get("MILVUS_HOST", "milvus-host")
MILVUS_PORT = os.environ.get("MILVUS_PORT", "19530")
MILVUS_USERNAME = os.environ.get("MILVUS_USERNAME", "")
MILVUS_PASSWORD = os.environ.get("MILVUS_PASSWORD", "")

# Redis配置
REDIS_HOST = os.environ.get('REDIS_HOST', 'redis-host')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
REDIS_DB = int(os.environ.get('REDIS_DB', 1))
REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', '')

# 文档处理配置
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
VECTOR_DIM = 1536  # OpenAI嵌入向量维度

# 模型配置 - 生产环境
# Chat模型配置
CHAT_MODEL_URL = os.environ.get("CHAT_MODEL_URL", "https://api.openai.com/v1/chat/completions")
CHAT_MODEL_API_KEY = os.environ.get("CHAT_MODEL_API_KEY", "")
CHAT_MODEL_NAME = os.environ.get("CHAT_MODEL_NAME", "gpt-3.5-turbo")

# Embedding模型配置
EMBEDDING_MODEL_URL = os.environ.get("EMBEDDING_MODEL_URL", "https://api.openai.com/v1/embeddings")
EMBEDDING_MODEL_API_KEY = os.environ.get("EMBEDDING_MODEL_API_KEY", "")
EMBEDDING_MODEL_NAME = os.environ.get("EMBEDDING_MODEL_NAME", "text-embedding-ada-002")

# Rerank模型配置
RERANK_MODEL_URL = os.environ.get("RERANK_MODEL_URL", "")
RERANK_MODEL_API_KEY = os.environ.get("RERANK_MODEL_API_KEY", "")
RERANK_MODEL_NAME = os.environ.get("RERANK_MODEL_NAME", "")

# 存储配置
STORAGE_MODE = os.environ.get("STORAGE_MODE", "minio")  # 生产环境默认使用MinIO

# MinIO配置
MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY", "")
MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY", "")
MINIO_SECURE = os.environ.get("MINIO_SECURE", "True").lower() == "true"
MINIO_BUCKET_NAME = os.environ.get("MINIO_BUCKET_NAME", "rag-documents")