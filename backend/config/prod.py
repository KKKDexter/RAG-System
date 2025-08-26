# 生产环境配置
import os
from typing import Any

# 注意：安全令牌配置（SECRET_KEY、ALGORITHM、ACCESS_TOKEN_EXPIRE_MINUTES）
# 已完全迁移到数据库中，不再从配置文件或环境变量加载
# 请使用 /v1/config/ API 或者数据库直接管理这些配置

# 数据库配置
# 从环境变量读取分开的数据库连接参数
DB_HOST = os.environ.get("DB_HOST", "db-host")
DB_USER = os.environ.get("DB_USER", "production_user")
DB_PASS = os.environ.get("DB_PASS", "production_password")
DB_NAME = os.environ.get("DB_NAME", "rag_system_prod")
DB_PORT = os.environ.get("DB_PORT", "3306")

# 构建 DATABASE_URL
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

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

# 文档处理配置（从环境变量读取）
CHUNK_SIZE = int(os.environ.get("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.environ.get("CHUNK_OVERLAP", "200"))
VECTOR_DIM = int(os.environ.get("VECTOR_DIM", "1536"))  # OpenAI嵌入向量维度

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