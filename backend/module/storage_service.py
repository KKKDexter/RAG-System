import os
import uuid
import asyncio
from typing import Tuple, Optional, BinaryIO, Union
from enum import Enum
from fastapi import HTTPException

# 根据环境变量动态导入配置
env = os.environ.get('ENVIRONMENT', 'dev')
if env == 'prod':
    from config.prod import STORAGE_MODE, MINIO_BUCKET_NAME
else:
    from config.dev import STORAGE_MODE, MINIO_BUCKET_NAME

# 导入存储服务
from module.minio_service import (
    minio_service, 
    upload_file_to_minio, 
    download_file_from_minio, 
    delete_file_from_minio,
    minio_file_exists,
    is_minio_available
)

# 导入日志配置
from logger_config import get_logger
logger = get_logger("storage_service")


class StorageType(Enum):
    """存储类型枚举"""
    LOCAL = "local"
    MINIO = "minio"
    BOTH = "both"


class StorageService:
    """统一存储服务类"""
    
    def __init__(self):
        """初始化存储服务"""
        self.storage_mode = StorageType(STORAGE_MODE.lower())
        logger.info(f"存储服务初始化，存储模式: {self.storage_mode.value}")
    
    async def save_file(self, file, folder_path: str = "documents", storage_type: Optional[StorageType] = None) -> dict:
        """
        保存文件到指定存储
        
        Args:
            file: 上传的文件对象
            folder_path: 文件夹路径
            storage_type: 指定存储类型，如果为None则使用默认配置
            
        Returns:
            dict: 存储结果信息
        """
        # 确定实际使用的存储类型
        actual_storage_type = storage_type or self.storage_mode
        
        result = {
            "storage_type": actual_storage_type.value,
            "local_path": None,
            "minio_path": None,
            "file_extension": None,
            "success": False,
            "error_message": None
        }
        
        try:
            # 获取文件扩展名
            original_filename = file.filename
            file_extension = os.path.splitext(original_filename)[1].lower()
            result["file_extension"] = file_extension
            
            logger.info(f"开始保存文件: {original_filename}，存储模式: {actual_storage_type.value}")
            
            # 判断是否需要本地存储
            needs_local_storage = actual_storage_type in [StorageType.LOCAL, StorageType.BOTH]
            
            if actual_storage_type == StorageType.LOCAL:
                # 仅本地存储
                if needs_local_storage:
                    local_path = await self._save_to_local(file, folder_path)
                    result["local_path"] = local_path
                    result["success"] = True
                    logger.info(f"文件保存到本地成功: {local_path}")
                
            elif actual_storage_type == StorageType.MINIO:
                # 仅MinIO存储
                if not is_minio_available():
                    raise HTTPException(status_code=500, detail="MinIO服务不可用")
                
                minio_path, _ = await upload_file_to_minio(file, folder_path)
                result["minio_path"] = minio_path
                result["success"] = True
                logger.info(f"文件保存到MinIO成功: {minio_path}")
                
            elif actual_storage_type == StorageType.BOTH:
                # 双存储模式
                try:
                    # 先保存到本地（如果需要）
                    if needs_local_storage:
                        local_path = await self._save_to_local(file, folder_path)
                        result["local_path"] = local_path
                    
                    # 再保存到MinIO
                    if is_minio_available():
                        # 重新读取文件内容用于MinIO上传
                        if hasattr(file, 'seek'):
                            file.seek(0)  # 重置文件指针
                        
                        minio_path, _ = await upload_file_to_minio(file, folder_path)
                        result["minio_path"] = minio_path
                        logger.info(f"文件保存到本地和MinIO成功: {result.get('local_path')}, {minio_path}")
                    else:
                        logger.warning("MinIO服务不可用，仅保存到本地")
                        
                    result["success"] = True
                    
                except Exception as e:
                    logger.error(f"双存储模式部分失败: {str(e)}")
                    # 即使部分失败，如果本地保存成功也算成功
                    if result["local_path"]:
                        result["success"] = True
                        result["error_message"] = f"MinIO保存失败: {str(e)}"
                    else:
                        raise e
            
            return result
            
        except Exception as e:
            error_msg = f"文件保存失败: {str(e)}"
            logger.error(error_msg)
            result["error_message"] = error_msg
            result["success"] = False
            raise HTTPException(status_code=500, detail=error_msg)
    
    async def _save_to_local(self, file, folder_path: str) -> str:
        """保存文件到本地"""
        # 创建上传目录
        upload_dir = self._create_upload_dir(folder_path)
        
        # 生成唯一文件名
        original_filename = file.filename
        file_extension = os.path.splitext(original_filename)[1].lower()
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        # 读取文件内容
        if hasattr(file, 'read'):
            if asyncio.iscoroutinefunction(file.read):
                content = await file.read()
            else:
                content = file.read()
        else:
            raise ValueError("不支持的文件对象类型")
        
        # 保存到本地
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        
        return file_path
    
    def _create_upload_dir(self, folder_path: str = "documents") -> str:
        """
        创建本地上传目录（只在需要本地存储时创建）
        
        Args:
            folder_path: 文件夹路径
            
        Returns:
            str: 本地目录路径
        """
        # 使用 documents 而不是 uploads 作为默认目录
        upload_dir = os.path.join(os.getcwd(), folder_path)
        
        try:
            # 只有在目录不存在时才创建
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir, exist_ok=True)
                logger.info(f"本地上传目录创建成功: {upload_dir}")
            else:
                logger.debug(f"本地上传目录已存在: {upload_dir}")
                
        except Exception as e:
            logger.error(f"本地上传目录创建失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"上传目录创建失败: {str(e)}")
            
        return upload_dir
    
    def get_file_content(self, file_path: str = None, minio_path: str = None) -> BinaryIO:
        """
        获取文件内容
        
        Args:
            file_path: 本地文件路径
            minio_path: MinIO文件路径
            
        Returns:
            BinaryIO: 文件内容流
        """
        try:
            # 优先从本地获取
            if file_path and os.path.exists(file_path):
                logger.info(f"从本地获取文件: {file_path}")
                return open(file_path, 'rb')
            
            # 从MinIO获取
            if minio_path and is_minio_available():
                logger.info(f"从MinIO获取文件: {minio_path}")
                return download_file_from_minio(minio_path)
            
            raise HTTPException(status_code=404, detail="文件不存在")
            
        except Exception as e:
            logger.error(f"获取文件内容失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"获取文件内容失败: {str(e)}")
    
    def delete_file(self, file_path: str = None, minio_path: str = None) -> dict:
        """
        删除文件
        
        Args:
            file_path: 本地文件路径
            minio_path: MinIO文件路径
            
        Returns:
            dict: 删除结果
        """
        result = {
            "local_deleted": False,
            "minio_deleted": False,
            "success": False,
            "error_message": None
        }
        
        try:
            # 删除本地文件
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    result["local_deleted"] = True
                    logger.info(f"本地文件删除成功: {file_path}")
                except Exception as e:
                    logger.error(f"本地文件删除失败: {str(e)}")
                    result["error_message"] = f"本地文件删除失败: {str(e)}"
            
            # 删除MinIO文件
            if minio_path and is_minio_available():
                try:
                    delete_file_from_minio(minio_path)
                    result["minio_deleted"] = True
                    logger.info(f"MinIO文件删除成功: {minio_path}")
                except Exception as e:
                    logger.error(f"MinIO文件删除失败: {str(e)}")
                    if not result["error_message"]:
                        result["error_message"] = f"MinIO文件删除失败: {str(e)}"
            
            # 只要有一个成功就算成功
            result["success"] = result["local_deleted"] or result["minio_deleted"]
            
            return result
            
        except Exception as e:
            error_msg = f"文件删除失败: {str(e)}"
            logger.error(error_msg)
            result["error_message"] = error_msg
            return result
    
    def file_exists(self, file_path: str = None, minio_path: str = None) -> bool:
        """
        检查文件是否存在
        
        Args:
            file_path: 本地文件路径
            minio_path: MinIO文件路径
            
        Returns:
            bool: 文件是否存在
        """
        # 检查本地文件
        if file_path and os.path.exists(file_path):
            return True
        
        # 检查MinIO文件
        if minio_path and is_minio_available():
            return minio_file_exists(minio_path)
        
        return False
    
    def get_storage_info(self) -> dict:
        """获取存储服务信息"""
        return {
            "storage_mode": self.storage_mode.value,
            "minio_available": is_minio_available(),
            "supported_types": [storage_type.value for storage_type in StorageType]
        }


# 全局存储服务实例
storage_service = StorageService()


# 便捷函数
async def save_file_to_storage(file, folder_path: str = "documents", storage_type: Optional[str] = None) -> dict:
    """
    保存文件到存储的便捷函数
    
    Args:
        file: 文件对象
        folder_path: 文件夹路径
        storage_type: 存储类型字符串
        
    Returns:
        dict: 存储结果
    """
    storage_type_enum = None
    if storage_type:
        try:
            storage_type_enum = StorageType(storage_type.lower())
        except ValueError:
            logger.warning(f"无效的存储类型: {storage_type}，使用默认配置")
    
    return await storage_service.save_file(file, folder_path, storage_type_enum)

def get_file_from_storage(file_path: str = None, minio_path: str = None) -> BinaryIO:
    """从存储获取文件的便捷函数"""
    return storage_service.get_file_content(file_path, minio_path)

def delete_file_from_storage(file_path: str = None, minio_path: str = None) -> dict:
    """从存储删除文件的便捷函数"""
    return storage_service.delete_file(file_path, minio_path)

def check_file_exists_in_storage(file_path: str = None, minio_path: str = None) -> bool:
    """检查文件是否存在于存储中的便捷函数"""
    return storage_service.file_exists(file_path, minio_path)

def get_storage_service_info() -> dict:
    """获取存储服务信息的便捷函数"""
    return storage_service.get_storage_info()