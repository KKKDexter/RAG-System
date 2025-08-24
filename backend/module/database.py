from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config.dev import DATABASE_URL

# 导入日志配置
from logger_config import get_logger
logger = get_logger("database")

# 创建数据库引擎
logger.info(f"正在创建数据库引擎: {DATABASE_URL}")
try:
    engine = create_engine(DATABASE_URL)
    logger.info("数据库引擎创建成功")
except Exception as e:
    logger.error(f"数据库引擎创建失败: {str(e)}")
    raise

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基础模型类
Base = declarative_base()

# 依赖项函数，获取数据库会话
def get_db():
    logger.debug("创建数据库会话")
    db = SessionLocal()
    try:
        logger.info("数据库会话创建成功")
        yield db
    except Exception as e:
        logger.error(f"数据库会话异常: {str(e)}")
        raise
    finally:
        logger.debug("关闭数据库会话")
        db.close()