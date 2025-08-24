import os
import sys
from fastapi import FastAPI
from contextlib import asynccontextmanager

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 打印当前工作目录和路径
print(f"当前工作目录: {os.getcwd()}")
print(f"当前文件路径: {os.path.abspath(__file__)}")
print(f"项目根目录: {os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}")

# 尝试加载.env文件和配置
try:
    print("\n尝试加载.env文件和配置...")
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    print(f"尝试加载.env文件: {env_path}")
    
    # 检查文件是否存在
    if os.path.exists(env_path):
        print(f".env文件存在，大小: {os.path.getsize(env_path)} 字节")
        # 加载.env文件
        load_dotenv(dotenv_path=env_path)
        print("已尝试加载.env文件")
    else:
        print(f"错误: .env文件不存在于路径 {env_path}")
        
    # 尝试导入配置
    from config.dev import SECRET_KEY, DATABASE_URL, MILVUS_HOST, REDIS_HOST
    print(f"从config.dev导入的SECRET_KEY: {SECRET_KEY}")
    print(f"从config.dev导入的DATABASE_URL: {DATABASE_URL}")
    print(f"从config.dev导入的MILVUS_HOST: {MILVUS_HOST}")
    print(f"从config.dev导入的REDIS_HOST: {REDIS_HOST}")
except Exception as e:
    print(f"加载配置失败: {str(e)}")

# 简化版的lifespan函数
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("应用初始化中...")
    print(f"使用的环境变量示例 - SECRET_KEY: {os.getenv('SECRET_KEY')}")
    yield
    print("应用关闭中...")

# 创建FastAPI应用
app = FastAPI(title="测试服务器", version="1.0.0", lifespan=lifespan)

# 简单的测试路由
@app.get("/")
def read_root():
    return {
        "status": "success",
        "message": "简化版服务器运行中",
        "env_vars": {
            "SECRET_KEY": os.getenv('SECRET_KEY'),
            "DATABASE_URL": os.getenv('DATABASE_URL')
        }
    }

if __name__ == "__main__":
    import uvicorn
    print("\n启动简化版服务器...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")