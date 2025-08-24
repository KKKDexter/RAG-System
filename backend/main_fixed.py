import os
import sys
import argparse
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 首先确保.env文件被加载
try:
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    print(f"尝试加载.env文件: {env_path}")
    if os.path.exists(env_path):
        load_dotenv(dotenv_path=env_path)
        print("已成功加载.env文件")
    else:
        print(f"警告: .env文件不存在于路径 {env_path}")
except Exception as e:
    print(f"加载.env文件时出错: {str(e)}")

# 解析命令行参数
parser = argparse.ArgumentParser(description="RAG系统后端服务")
parser.add_argument("--port", type=int, default=8000, help="服务端口")
parser.add_argument("--env", type=str, default="dev", help="运行环境 dev/prod")
args = parser.parse_args()

# 设置环境变量
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入配置和路由 - 在加载.env文件后进行
try:
    from config.dev import (MILVUS_HOST, MILVUS_PORT,
                            SECRET_KEY, ALGORITHM)
    print(f"从config.dev导入的SECRET_KEY: {SECRET_KEY}")
    print(f"从config.dev导入的MILVUS_HOST: {MILVUS_HOST}")
    
    from api.auth import router as auth_router
    from api.rag import router as rag_router
    from api.users import router as users_router
    from api.llm import router as llm_router
    
    # 导入数据库和Milvus相关模块
    from module.database import Base, engine
    from module.milvus_service import connect_to_milvus
    from module.document_service import create_upload_dir
    
    # 导入日志配置
    from logger_config import get_logger
    logger = get_logger("main")
except Exception as e:
    print(f"导入模块时出错: {str(e)}")
    # 在实际部署中，可以选择退出或使用默认配置
    # 这里我们继续，但在实际运行中可能会有其他错误

# 使用lifespan事件处理器替代on_event
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("开始初始化应用...")
    
    # 创建数据库表
    try:
        Base.metadata.create_all(bind=engine)
        print("数据库表创建成功")
    except Exception as e:
        print(f"创建数据库表失败: {str(e)}")
    
    # 连接Milvus
    try:
        connect_to_milvus()
        print(f"Milvus连接成功: {MILVUS_HOST}:{MILVUS_PORT}")
    except Exception as e:
        print(f"Milvus连接失败: {str(e)}")
    
    # 创建上传目录
    try:
        create_upload_dir()
    except Exception as e:
        print(f"创建上传目录失败: {str(e)}")
    
    # 应用启动成功
    print("应用初始化完成，等待请求...")
    
    # yield之后的代码会在应用关闭时执行
    yield
    
    # 这里可以添加应用关闭时的清理逻辑
    print("应用正在关闭...")

# 创建FastAPI应用
app = FastAPI(title="RAG系统API", version="1.0.0", lifespan=lifespan)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth_router)
app.include_router(rag_router)
app.include_router(users_router)
app.include_router(llm_router)

if __name__ == "__main__":
    import uvicorn
    print(f"启动RAG系统后端服务 - 环境: {args.env}, 端口: {args.port}")
    uvicorn.run(app, host="0.0.0.0", port=args.port, log_level="info")