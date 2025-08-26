# 开发环境配置
import os
from typing import Any
from dotenv import load_dotenv

# 加载.env文件中的环境变量 - 使用项目根目录下的.env文件
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path=env_path)

# 注意：安全令牌配置（SECRET_KEY、ALGORITHM、ACCESS_TOKEN_EXPIRE_MINUTES）
# 已完全迁移到数据库中，不再从配置文件加载
# 请使用 /v1/config/ API 或者数据库直接管理这些配置

# 数据库配置
# 从环境变量读取分开的数据库连接参数
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASS", "password")
DB_NAME = os.getenv("DB_NAME", "rag_system")
DB_PORT = os.getenv("DB_PORT", "3306")

# 构建 DATABASE_URL
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Milvus配置
MILVUS_HOST = os.getenv("MILVUS_HOST", "localhost")
MILVUS_PORT = os.getenv("MILVUS_PORT", "19530")
MILVUS_USERNAME = os.getenv("MILVUS_USERNAME", "")
MILVUS_PASSWORD = os.getenv("MILVUS_PASSWORD", "")

# Redis配置
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
REDIS_DB = int(os.getenv('REDIS_DB', '0'))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', "")

# 文档处理配置（从.env文件读取）
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))
VECTOR_DIM = int(os.getenv("VECTOR_DIM", "1536"))  # OpenAI嵌入向量维度

# 模型配置 - 开发环境
# Chat模型配置
CHAT_MODEL_URL = os.getenv("CHAT_MODEL_URL", "https://api.openai.com/v1/chat/completions")
CHAT_MODEL_API_KEY = os.getenv("CHAT_MODEL_API_KEY", "your-openai-api-key")
CHAT_MODEL_NAME = os.getenv("CHAT_MODEL_NAME", "gpt-3.5-turbo")

# Embedding模型配置
EMBEDDING_MODEL_URL = os.getenv("EMBEDDING_MODEL_URL", "https://api.openai.com/v1/embeddings")
EMBEDDING_MODEL_API_KEY = os.getenv("EMBEDDING_MODEL_API_KEY", "your-openai-api-key")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "text-embedding-ada-002")

# Rerank模型配置
RERANK_MODEL_URL = os.getenv("RERANK_MODEL_URL", "")
RERANK_MODEL_API_KEY = os.getenv("RERANK_MODEL_API_KEY", "")
RERANK_MODEL_NAME = os.getenv("RERANK_MODEL_NAME", "")

# 存储配置
STORAGE_MODE = os.getenv("STORAGE_MODE", "local")  # local, minio, both

# MinIO配置
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "")
MINIO_SECURE = os.getenv("MINIO_SECURE", "False").lower() == "true"
MINIO_BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME", "rag-documents")