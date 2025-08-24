import os
from dotenv import load_dotenv

# 打印当前工作目录
print(f"当前工作目录: {os.getcwd()}")

# 手动加载.env文件
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
print(f"尝试加载.env文件: {env_path}")

# 检查文件是否存在
if os.path.exists(env_path):
    print(f".env文件存在，大小: {os.path.getsize(env_path)} 字节")
    # 加载.env文件
    load_dotenv(dotenv_path=env_path)
    print("已尝试加载.env文件")
    
    # 打印一些环境变量
    print(f"SECRET_KEY: {os.getenv('SECRET_KEY')}")
    print(f"DATABASE_URL: {os.getenv('DATABASE_URL')}")
    print(f"MILVUS_HOST: {os.getenv('MILVUS_HOST')}")
    print(f"REDIS_HOST: {os.getenv('REDIS_HOST')}")
else:
    print(f"错误: .env文件不存在于路径 {env_path}")
    
# 尝试直接从config.dev导入配置
try:
    print("\n尝试从config.dev导入配置...")
    from config.dev import SECRET_KEY, DATABASE_URL, MILVUS_HOST, REDIS_HOST
    print(f"从config.dev导入的SECRET_KEY: {SECRET_KEY}")
    print(f"从config.dev导入的DATABASE_URL: {DATABASE_URL}")
    print(f"从config.dev导入的MILVUS_HOST: {MILVUS_HOST}")
    print(f"从config.dev导入的REDIS_HOST: {REDIS_HOST}")
except Exception as e:
    print(f"从config.dev导入配置失败: {str(e)}")