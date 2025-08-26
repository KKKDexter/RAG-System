import os
import sys
import argparse
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ✅ 修复 functools.iscoroutinefunction 兼容性问题
import inspect, functools
if not hasattr(functools, "iscoroutinefunction"):
    functools.iscoroutinefunction = inspect.iscoroutinefunction

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
auth_router = None
rag_router = None
users_router = None
admin_router = None
llm_router = None
config_router = None
MILVUS_HOST = None
MILVUS_PORT = None
logger = None
create_upload_dir = None

# 先导入基础模块（避免在lifespan中出现未定义错误）
try:
    from module.database import Base, engine
    from module.milvus_service import connect_to_milvus
    from module.storage_service import create_upload_dir
    print("[DEBUG] 基础模块导入成功")
except Exception as e:
    print(f"[ERROR] 基础模块导入失败: {str(e)}")
    Base = None
    engine = None
    connect_to_milvus = None
    create_upload_dir = None

try:
    # 根据环境参数动态导入配置
    if args.env == 'prod':
        from config.prod import MILVUS_HOST, MILVUS_PORT
        print(f"使用生产环境配置: MILVUS_HOST={MILVUS_HOST}")
    else:
        from config.dev import MILVUS_HOST, MILVUS_PORT
        print(f"使用开发环境配置: MILVUS_HOST={MILVUS_HOST}")
    
    print("[INFO] 安全配置（SECRET_KEY、ALGORITHM）已从数据库动态加载")
    
    # 先导入认证路由（最重要）
    from api.auth import router as auth_router
    print("[DEBUG] 成功导入 auth_router")
    
    # 导入用户路由（次重要）
    from api.users import router as users_router, admin_router
    print("[DEBUG] 成功导入 users_router 和 admin_router")
    
    # 导入其他路由（允许失败）
    try:
        from api.rag import router as rag_router
        print("[DEBUG] 成功导入 rag_router")
    except Exception as e:
        print(f"[WARNING] 导入 rag_router 失败: {str(e)}")
        rag_router = None
    
    try:
        from api.llm import router as llm_router
        print("[DEBUG] 成功导入 llm_router")
    except Exception as e:
        print(f"[WARNING] 导入 llm_router 失败: {str(e)}")
        llm_router = None
    
    try:
        from api.config import router as config_router
        print("[DEBUG] 成功导入 config_router")
    except Exception as e:
        print(f"[WARNING] 导入 config_router 失败: {str(e)}")
        config_router = None
    
    # 导入日志配置
    from logger_config import get_logger
    logger = get_logger("main")
    
    print("[SUCCESS] 核心模块导入成功")
except Exception as e:
    print(f"导入模块时出错: {str(e)}")
    print("[WARNING] 部分模块导入失败，但核心功能应该可用")
    # 设置默认值以避免后续错误
    if MILVUS_HOST is None:
        MILVUS_HOST = "localhost"
        MILVUS_PORT = "19530"
    
    # 确保核心路由存在
    if 'auth_router' not in locals():
        auth_router = None
        print("[ERROR] 认证路由导入失败")
    if 'users_router' not in locals():
        users_router = None
        admin_router = None
        print("[ERROR] 用户路由导入失败")

# 使用lifespan事件处理器替代on_event
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("开始初始化应用...")
    
    # 创建数据库表
    try:
        if Base is not None and engine is not None:
            Base.metadata.create_all(bind=engine)
            print("数据库表创建成功")
        else:
            print("数据库模块未成功导入，跳过表创建")
    except Exception as e:
        print(f"创建数据库表失败: {str(e)}")
    
    # 加载动态配置（从数据库加载安全令牌配置）
    try:
        from module.config_manager import update_runtime_config
        if update_runtime_config():
            print("动态配置加载成功")
        else:
            print("动态配置加载失败，使用默认配置")
    except Exception as e:
        print(f"加载动态配置时出错: {str(e)}")
    
    # 连接Milvus
    try:
        if connect_to_milvus is not None and MILVUS_HOST is not None:
            connect_to_milvus()
            print(f"Milvus连接成功: {MILVUS_HOST}:{MILVUS_PORT}")
        else:
            print("Milvus模块未成功导入，跳过连接")
    except Exception as e:
        print(f"Milvus连接失败: {str(e)}")
    
    # 创建上传目录
    try:
        if create_upload_dir is not None:
            create_upload_dir()
        else:
            print("文档服务模块未成功导入，跳过上传目录创建")
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

# 注册路由（优先注册核心路由）
print("\n[INFO] 开始注册路由...")

# 核心路由：认证和用户管理
if auth_router:
    app.include_router(auth_router)
    print("[DEBUG] ✅ 已注册 auth_router: /v1/auth/*")
else:
    print("[ERROR] ❌ auth_router 注册失败")

if users_router:
    app.include_router(users_router)
    print("[DEBUG] ✅ 已注册 users_router: /v1/users/*")
else:
    print("[ERROR] ❌ users_router 注册失败")

if admin_router:
    app.include_router(admin_router)
    print("[DEBUG] ✅ 已注册 admin_router: /v1/admin/*")
else:
    print("[ERROR] ❌ admin_router 注册失败")

# 可选路由：其他功能
if rag_router:
    app.include_router(rag_router)
    print("[DEBUG] ✅ 已注册 rag_router: /v1/rag/*")
else:
    print("[WARNING] ⚠️ rag_router 未注册")

if llm_router:
    app.include_router(llm_router)
    print("[DEBUG] ✅ 已注册 llm_router: /llm/*")
else:
    print("[WARNING] ⚠️ llm_router 未注册")

if config_router:
    app.include_router(config_router)
    print("[DEBUG] ✅ 已注册 config_router: /v1/config/*")
else:
    print("[WARNING] ⚠️ config_router 未注册")

print(f"\n[INFO] 路由注册完成，应用包含 {len(app.routes)} 个路由")

# 显示所有注册的路由
print("[DEBUG] 所有注册的路由:")
for route in app.routes:
    if hasattr(route, 'path') and hasattr(route, 'methods'):
        print(f"  {route.path} - {route.methods}")

if __name__ == "__main__":
    import uvicorn
    print(f"启动RAG系统后端服务 - 环境: {args.env}, 端口: {args.port}")
    uvicorn.run(app, host="0.0.0.0", port=args.port, log_level="info")
