from loguru import logger
import os
import sys

# 确保日志目录存在
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'log')
os.makedirs(log_dir, exist_ok=True)

# 定义日志格式
log_format = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"

# 清除默认的控制台输出
logger.remove()

# 添加控制台输出
logger.add(
    sys.stdout,
    format=log_format,
    level="DEBUG",
    colorize=True
)

# 添加文件输出 - 全部日志
logger.add(
    os.path.join(log_dir, "app.log"),
    format=log_format,
    level="DEBUG",
    rotation="100 MB",
    retention="7 days",
    compression="zip",
    encoding="utf-8"
)

# 添加错误日志文件输出
logger.add(
    os.path.join(log_dir, "error.log"),
    format=log_format,
    level="ERROR",
    rotation="100 MB",
    retention="30 days",
    compression="zip",
    encoding="utf-8"
)

# 添加JSON格式的日志输出，便于日志分析
logger.add(
    os.path.join(log_dir, "app.json"),
    format="{{"time":"{time:YYYY-MM-DD HH:mm:ss.SSS}","level":"{level}","module":"{name}","function":"{function}","line":{line},"message":"{message}"}}\n",
    level="INFO",
    rotation="1 day",
    retention="30 days",
    compression="zip",
    encoding="utf-8"
)

def get_logger(name=None):
    """获取配置好的logger实例"""
    if name:
        return logger.bind(module=name)
    return logger