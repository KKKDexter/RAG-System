# 开发环境配置
import os
from dotenv import load_dotenv

# 加载.env文件中的环境变量 - 使用项目根目录下的.env文件
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path=env_path)

# 安全配置
SECRET_KEY = os.getenv("SECRET_KEY", "02lkAtLdaHZbln18tm37mAGdgo90wke8")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# 数据库配置
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:password@localhost/rag_system")

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

# 文档处理配置
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