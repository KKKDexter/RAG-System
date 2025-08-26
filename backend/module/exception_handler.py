"""
通用异常处理模块

本模块提供统一的异常处理装饰器和工具函数，避免重复的异常处理逻辑

作者: RAG-System Team
版本: 1.0
"""

# ✅ 修复 functools.iscoroutinefunction 兼容性问题
import inspect
import functools
if not hasattr(functools, "iscoroutinefunction"):
    functools.iscoroutinefunction = inspect.iscoroutinefunction

from typing import Any, Callable, Dict, Optional
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from logger_config import get_logger

logger = get_logger("exception_handler")

# ====================
# 常见异常映射
# ====================

COMMON_EXCEPTIONS = {
    # 数据库相关异常
    IntegrityError: {
        "status_code": status.HTTP_400_BAD_REQUEST,
        "detail": "数据完整性约束冲突"
    },
    SQLAlchemyError: {
        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "detail": "数据库操作失败"
    },
    # 通用异常
    ValueError: {
        "status_code": status.HTTP_400_BAD_REQUEST,
        "detail": "输入参数错误"
    },
    KeyError: {
        "status_code": status.HTTP_400_BAD_REQUEST,
        "detail": "缺少必需的参数"
    },
    FileNotFoundError: {
        "status_code": status.HTTP_404_NOT_FOUND,
        "detail": "文件不存在"
    },
    PermissionError: {
        "status_code": status.HTTP_403_FORBIDDEN,
        "detail": "权限不足"
    }
}

# ====================
# 异常处理装饰器
# ====================

def handle_exceptions(
    operation_name: str = "操作",
    success_message: Optional[str] = None,
    custom_exceptions: Optional[Dict] = None
):
    """
    统一异常处理装饰器
    
    Args:
        operation_name (str): 操作名称，用于日志记录
        success_message (Optional[str]): 成功消息
        custom_exceptions (Optional[Dict]): 自定义异常映射
    
    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                logger.debug(f"开始执行{operation_name}: {func.__name__}")
                result = func(*args, **kwargs)
                
                if success_message:
                    logger.info(f"{operation_name}成功: {success_message}")
                else:
                    logger.info(f"{operation_name}成功: {func.__name__}")
                
                return result
                
            except HTTPException:
                # FastAPI HTTPException 直接抛出
                raise
            except Exception as e:
                logger.error(f"{operation_name}失败: {func.__name__}, 错误: {str(e)}")
                
                # 检查自定义异常映射
                exception_map = {**COMMON_EXCEPTIONS}
                if custom_exceptions:
                    exception_map.update(custom_exceptions)
                
                # 查找匹配的异常类型
                for exc_type, config in exception_map.items():
                    if isinstance(e, exc_type):
                        raise HTTPException(
                            status_code=config["status_code"],
                            detail=f"{config['detail']}: {str(e)}"
                        )
                
                # 未知异常，返回500错误
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"{operation_name}失败: {str(e)}"
                )
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                logger.debug(f"开始执行{operation_name}: {func.__name__}")
                result = await func(*args, **kwargs)
                
                if success_message:
                    logger.info(f"{operation_name}成功: {success_message}")
                else:
                    logger.info(f"{operation_name}成功: {func.__name__}")
                
                return result
                
            except HTTPException:
                # FastAPI HTTPException 直接抛出
                raise
            except Exception as e:
                logger.error(f"{operation_name}失败: {func.__name__}, 错误: {str(e)}")
                
                # 检查自定义异常映射
                exception_map = {**COMMON_EXCEPTIONS}
                if custom_exceptions:
                    exception_map.update(custom_exceptions)
                
                # 查找匹配的异常类型
                for exc_type, config in exception_map.items():
                    if isinstance(e, exc_type):
                        raise HTTPException(
                            status_code=config["status_code"],
                            detail=f"{config['detail']}: {str(e)}"
                        )
                
                # 未知异常，返回500错误
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"{operation_name}失败: {str(e)}"
                )
        
        # 根据函数类型返回相应的包装器
        return async_wrapper if functools.iscoroutinefunction(func) else sync_wrapper
    
    return decorator

# ====================
# 专用异常处理装饰器
# ====================

def handle_database_exceptions(operation_name: str = "数据库操作"):
    """
    数据库操作异常处理装饰器
    
    Args:
        operation_name (str): 操作名称
    
    Returns:
        装饰器函数
    """
    custom_exceptions = {
        IntegrityError: {
            "status_code": status.HTTP_409_CONFLICT,
            "detail": "数据已存在或违反唯一性约束"
        }
    }
    return handle_exceptions(operation_name, custom_exceptions=custom_exceptions)

def handle_file_exceptions(operation_name: str = "文件操作"):
    """
    文件操作异常处理装饰器
    
    Args:
        operation_name (str): 操作名称
    
    Returns:
        装饰器函数
    """
    custom_exceptions = {
        FileNotFoundError: {
            "status_code": status.HTTP_404_NOT_FOUND,
            "detail": "文件不存在"
        },
        PermissionError: {
            "status_code": status.HTTP_403_FORBIDDEN,
            "detail": "文件权限不足"
        },
        IsADirectoryError: {
            "status_code": status.HTTP_400_BAD_REQUEST,
            "detail": "目标是一个目录"
        }
    }
    return handle_exceptions(operation_name, custom_exceptions=custom_exceptions)

def handle_api_exceptions(operation_name: str = "API调用"):
    """
    API调用异常处理装饰器
    
    Args:
        operation_name (str): 操作名称
    
    Returns:
        装饰器函数
    """
    custom_exceptions = {
        ConnectionError: {
            "status_code": status.HTTP_503_SERVICE_UNAVAILABLE,
            "detail": "外部服务连接失败"
        },
        TimeoutError: {
            "status_code": status.HTTP_504_GATEWAY_TIMEOUT,
            "detail": "外部服务响应超时"
        }
    }
    return handle_exceptions(operation_name, custom_exceptions=custom_exceptions)

# ====================
# 通用工具函数
# ====================

def raise_not_found(resource_name: str, resource_id: Any = None):
    """
    抛出资源不存在异常
    
    Args:
        resource_name (str): 资源名称
        resource_id (Any): 资源ID（可选）
    
    Raises:
        HTTPException: 404错误
    """
    detail = f"{resource_name}不存在"
    if resource_id is not None:
        detail += f" (ID: {resource_id})"
    
    logger.warning(detail)
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=detail
    )

def raise_conflict(resource_name: str, message: str = "资源已存在"):
    """
    抛出资源冲突异常
    
    Args:
        resource_name (str): 资源名称
        message (str): 错误消息
    
    Raises:
        HTTPException: 409错误
    """
    detail = f"{resource_name}{message}"
    logger.warning(detail)
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=detail
    )

def raise_validation_error(field_name: str, message: str):
    """
    抛出参数验证异常
    
    Args:
        field_name (str): 字段名称
        message (str): 错误消息
    
    Raises:
        HTTPException: 400错误
    """
    detail = f"{field_name}: {message}"
    logger.warning(f"参数验证失败: {detail}")
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=detail
    )

# ====================
# 快捷装饰器
# ====================

# 常用操作的快捷装饰器
create_resource = lambda name: handle_database_exceptions(f"创建{name}")
update_resource = lambda name: handle_database_exceptions(f"更新{name}")
delete_resource = lambda name: handle_database_exceptions(f"删除{name}")
get_resource = lambda name: handle_exceptions(f"获取{name}")
upload_file = lambda: handle_file_exceptions("文件上传")
download_file = lambda: handle_file_exceptions("文件下载")