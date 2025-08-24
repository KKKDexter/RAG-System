import os
import sys
import argparse
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 导入日志配置
from logger_config import get_logger
logger = get_logger("main")

# 命令行参数解析
def parse_arguments():
    parser = argparse.ArgumentParser(description="RAG系统后端服务")
    parser.add_argument("--env", type=str, default="dev", choices=["dev", "prod"], 
                        help="运行环境: dev (开发环境) 或 prod (生产环境)")
    parser.add_argument("--port", type=int, default=8000, 
                        help="服务端口号，默认8000")
    return parser.parse_args()

# 获取命令行参数
args = parse_arguments()

# 设置环境变量，供其他模块使用
os.environ['ENVIRONMENT'] = args.env
logger.info(f"设置运行环境: {args.env}")

# 根据环境动态导入配置
env_config = __import__(f"config.{args.env}", fromlist=["*"])

# 导入各个模块
from module.database import Base, engine
from module.milvus_service import connect_to_milvus
from module.document_service import create_upload_dir

# 导入路由
from api.auth import router as auth_router
from api.rag import router as rag_router
from api.users import router as users_router, admin_router
from api.llm import router as llm_router

# 创建FastAPI应用
app = FastAPI(title="RAG系统API", version="1.0.0")

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
app.include_router(admin_router)

# 启动应用时初始化
@app.on_event("startup")
def startup_event():
    logger.info("开始初始化应用...")
    
    # 创建数据库表
    logger.debug("创建数据库表...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("数据库表创建成功")
    except Exception as e:
        logger.error(f"创建数据库表失败: {str(e)}")
    
    # 连接Milvus
    logger.debug("连接Milvus向量数据库...")
    try:
        connect_to_milvus()
        logger.info(f"Milvus连接成功: {MILVUS_HOST}:{MILVUS_PORT}")
    except Exception as e:
        logger.error(f"Milvus连接失败: {str(e)}")
    
    # 创建上传目录
    logger.debug("创建上传目录...")
    try:
        create_upload_dir()
        logger.info("上传目录创建成功")
    except Exception as e:
        logger.error(f"上传目录创建失败: {str(e)}")
    
    logger.info("应用初始化完成")

if __name__ == "__main__":
    import uvicorn
    logger.info(f"启动RAG系统后端服务 - 环境: {args.env}, 端口: {args.port}")
    uvicorn.run(app, host="0.0.0.0", port=args.port, log_config=None)