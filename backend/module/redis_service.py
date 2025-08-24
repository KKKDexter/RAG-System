import os
import hashlib
import redis

# 根据环境变量动态导入配置
env = os.environ.get('ENVIRONMENT', 'dev')
if env == 'prod':
    from config.prod import REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD
else:
    from config.dev import REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD

# 导入日志配置
from logger_config import get_logger
logger = get_logger("redis_service")

# 创建Redis客户端配置
redis_config = {
    "host": REDIS_HOST,
    "port": REDIS_PORT,
    "db": REDIS_DB
}

# 如果设置了密码，则添加密码配置
if REDIS_PASSWORD:
    redis_config["password"] = REDIS_PASSWORD
    logger.debug("Redis连接包含密码认证")

# 创建Redis客户端
logger.info(f"尝试连接Redis服务器: {REDIS_HOST}:{REDIS_PORT}, 数据库: {REDIS_DB}")
try:
    redis_client = redis.Redis(**redis_config)
    # 测试连接
    redis_client.ping()
    logger.info("Redis服务器连接成功")
except Exception as e:
    logger.error(f"Redis服务器连接失败: {str(e)}")
    # 继续创建客户端，让应用可以尝试重新连接
    redis_client = redis.Redis(**redis_config)

# 缓存问答结果
def cache_qa_result(user_id: int, question: str, answer: str, expire: int = 3600) -> None:
    logger.info(f"缓存用户 {user_id} 的问答结果，过期时间: {expire} 秒")
    logger.debug(f"问题摘要: {question[:30]}{'...' if len(question) > 30 else ''}")
    
    try:
        cache_key = f"qa:cache:{hashlib.md5(f'{user_id}:{question}'.encode()).hexdigest()}"
        redis_client.set(cache_key, answer, ex=expire)
        logger.debug(f"问答结果缓存成功，缓存键: {cache_key}")
    except Exception as e:
        logger.error(f"缓存问答结果失败: {str(e)}")
        # 不抛出异常，允许应用继续运行

# 获取缓存的问答结果
def get_cached_qa_result(user_id: int, question: str) -> str:
    logger.info(f"获取用户 {user_id} 的缓存问答结果")
    logger.debug(f"问题摘要: {question[:30]}{'...' if len(question) > 30 else ''}")
    
    try:
        cache_key = f"qa:cache:{hashlib.md5(f'{user_id}:{question}'.encode()).hexdigest()}"
        cached_answer = redis_client.get(cache_key)
        
        if cached_answer:
            logger.info(f"找到缓存的问答结果，缓存键: {cache_key}")
            return cached_answer.decode()
        else:
            logger.debug(f"未找到缓存的问答结果，缓存键: {cache_key}")
            return None
    except Exception as e:
        logger.error(f"获取缓存问答结果失败: {str(e)}")
        # 不抛出异常，允许应用继续运行
        return None