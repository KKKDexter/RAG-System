import os
import uuid
import asyncio
from typing import Tuple, Optional, BinaryIO
from io import BytesIO
from fastapi import HTTPException
from minio import Minio
from minio.error import S3Error

# 根据环境变量动态导入配置
env = os.environ.get('ENVIRONMENT', 'dev')
if env == 'prod':
    from config.prod import MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_SECURE, MINIO_BUCKET_NAME
else:
    from config.dev import MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_SECURE, MINIO_BUCKET_NAME

# 导入日志配置
from logger_config import get_logger
logger = get_logger("minio_service")


class MinIOService:
    """MinIO对象存储服务类"""
    
    def __init__(self):
        """初始化MinIO客户端"""
        try:
            # 检查MinIO配置
            if not all([MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_BUCKET_NAME]):
                logger.warning("MinIO配置不完整，MinIO服务将不可用")
                self.client = None
                return
            
            # 创建MinIO客户端
            self.client = Minio(
                MINIO_ENDPOINT,
                access_key=MINIO_ACCESS_KEY,
                secret_key=MINIO_SECRET_KEY,
                secure=MINIO_SECURE
            )
            
            # 确保存储桶存在
            self._ensure_bucket_exists()
            logger.info(f"MinIO服务初始化成功，连接到: {MINIO_ENDPOINT}")
            
        except Exception as e:
            logger.error(f"MinIO服务初始化失败: {str(e)}")
            self.client = None
    
    def _ensure_bucket_exists(self):
        """确保存储桶存在"""
        try:
            if not self.client.bucket_exists(MINIO_BUCKET_NAME):
                self.client.make_bucket(MINIO_BUCKET_NAME)
                logger.info(f"创建MinIO存储桶: {MINIO_BUCKET_NAME}")
            else:
                logger.debug(f"MinIO存储桶已存在: {MINIO_BUCKET_NAME}")
        except S3Error as e:
            logger.error(f"MinIO存储桶操作失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"MinIO存储桶操作失败: {str(e)}")
    
    def is_available(self) -> bool:
        """检查MinIO服务是否可用"""
        return self.client is not None
    
    async def upload_file(self, file, folder_path: str = "documents") -> Tuple[str, str]:
        """
        上传文件到MinIO
        
        Args:
            file: 上传的文件对象
            folder_path: 文件夹路径
            
        Returns:
            Tuple[str, str]: (MinIO对象名, 文件扩展名)
        """
        if not self.is_available():
            raise HTTPException(status_code=500, detail="MinIO服务不可用")
        
        try:
            # 获取文件信息
            original_filename = file.filename
            file_extension = os.path.splitext(original_filename)[1].lower()
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            object_name = f"{folder_path}/{unique_filename}"
            
            logger.info(f"开始上传文件到MinIO: {original_filename} -> {object_name}")
            
            # 读取文件内容
            if hasattr(file, 'read'):
                if asyncio.iscoroutinefunction(file.read):
                    content = await file.read()
                else:
                    content = file.read()
            else:
                raise ValueError("不支持的文件对象类型")
            
            # 上传到MinIO
            self.client.put_object(
                MINIO_BUCKET_NAME,
                object_name,
                BytesIO(content),
                length=len(content),
                content_type=self._get_content_type(file_extension)
            )
            
            logger.info(f"文件上传到MinIO成功: {object_name}，大小: {len(content)} 字节")
            return object_name, file_extension
            
        except S3Error as e:
            logger.error(f"MinIO文件上传失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"MinIO文件上传失败: {str(e)}")
        except Exception as e:
            logger.error(f"文件上传处理失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"文件上传处理失败: {str(e)}")
    
    def download_file(self, object_name: str) -> BinaryIO:
        """
        从MinIO下载文件
        
        Args:
            object_name: MinIO对象名
            
        Returns:
            BinaryIO: 文件流
        """
        if not self.is_available():
            raise HTTPException(status_code=500, detail="MinIO服务不可用")
        
        try:
            logger.info(f"从MinIO下载文件: {object_name}")
            response = self.client.get_object(MINIO_BUCKET_NAME, object_name)
            return response
        except S3Error as e:
            logger.error(f"MinIO文件下载失败: {str(e)}")
            raise HTTPException(status_code=404, detail=f"文件不存在: {object_name}")
        except Exception as e:
            logger.error(f"文件下载处理失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"文件下载处理失败: {str(e)}")
    
    def delete_file(self, object_name: str) -> bool:
        """
        从MinIO删除文件
        
        Args:
            object_name: MinIO对象名
            
        Returns:
            bool: 删除是否成功
        """
        if not self.is_available():
            raise HTTPException(status_code=500, detail="MinIO服务不可用")
        
        try:
            logger.info(f"从MinIO删除文件: {object_name}")
            self.client.remove_object(MINIO_BUCKET_NAME, object_name)
            logger.info(f"MinIO文件删除成功: {object_name}")
            return True
        except S3Error as e:
            logger.error(f"MinIO文件删除失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"MinIO文件删除失败: {str(e)}")
        except Exception as e:
            logger.error(f"文件删除处理失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"文件删除处理失败: {str(e)}")
    
    def file_exists(self, object_name: str) -> bool:
        """
        检查MinIO中文件是否存在
        
        Args:
            object_name: MinIO对象名
            
        Returns:
            bool: 文件是否存在
        """
        if not self.is_available():
            return False
        
        try:
            self.client.stat_object(MINIO_BUCKET_NAME, object_name)
            return True
        except S3Error:
            return False
        except Exception as e:
            logger.error(f"检查文件存在性失败: {str(e)}")
            return False
    
    def get_file_info(self, object_name: str) -> Optional[dict]:
        """
        获取MinIO中文件信息
        
        Args:
            object_name: MinIO对象名
            
        Returns:
            Optional[dict]: 文件信息字典
        """
        if not self.is_available():
            return None
        
        try:
            stat = self.client.stat_object(MINIO_BUCKET_NAME, object_name)
            return {
                "size": stat.size,
                "last_modified": stat.last_modified,
                "etag": stat.etag,
                "content_type": stat.content_type
            }
        except S3Error as e:
            logger.error(f"获取MinIO文件信息失败: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"文件信息获取处理失败: {str(e)}")
            return None
    
    def list_files(self, prefix: str = "") -> list:
        """
        列出MinIO中的文件
        
        Args:
            prefix: 文件名前缀过滤
            
        Returns:
            list: 文件对象列表
        """
        if not self.is_available():
            return []
        
        try:
            objects = self.client.list_objects(MINIO_BUCKET_NAME, prefix=prefix, recursive=True)
            file_list = []
            for obj in objects:
                file_list.append({
                    "object_name": obj.object_name,
                    "size": obj.size,
                    "last_modified": obj.last_modified,
                    "etag": obj.etag
                })
            return file_list
        except S3Error as e:
            logger.error(f"列出MinIO文件失败: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"文件列表获取处理失败: {str(e)}")
            return []
    
    def get_file_url(self, object_name: str, expires: int = 3600) -> Optional[str]:
        """
        生成MinIO文件的预签名URL
        
        Args:
            object_name: MinIO对象名
            expires: URL过期时间（秒）
            
        Returns:
            Optional[str]: 预签名URL
        """
        if not self.is_available():
            return None
        
        try:
            url = self.client.presigned_get_object(MINIO_BUCKET_NAME, object_name, expires=expires)
            return url
        except S3Error as e:
            logger.error(f"生成MinIO预签名URL失败: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"URL生成处理失败: {str(e)}")
            return None
    
    def _get_content_type(self, file_extension: str) -> str:
        """
        根据文件扩展名获取Content-Type
        
        Args:
            file_extension: 文件扩展名
            
        Returns:
            str: Content-Type
        """
        content_types = {
            '.pdf': 'application/pdf',
            '.txt': 'text/plain',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.doc': 'application/msword',
            '.md': 'text/markdown'
        }
        return content_types.get(file_extension.lower(), 'application/octet-stream')


# 全局MinIO服务实例
minio_service = MinIOService()


# 便捷函数
async def upload_file_to_minio(file, folder_path: str = "documents") -> Tuple[str, str]:
    """上传文件到MinIO的便捷函数"""
    return await minio_service.upload_file(file, folder_path)

def download_file_from_minio(object_name: str) -> BinaryIO:
    """从MinIO下载文件的便捷函数"""
    return minio_service.download_file(object_name)

def delete_file_from_minio(object_name: str) -> bool:
    """从MinIO删除文件的便捷函数"""
    return minio_service.delete_file(object_name)

def minio_file_exists(object_name: str) -> bool:
    """检查MinIO文件是否存在的便捷函数"""
    return minio_service.file_exists(object_name)

def get_minio_file_info(object_name: str) -> Optional[dict]:
    """获取MinIO文件信息的便捷函数"""
    return minio_service.get_file_info(object_name)

def is_minio_available() -> bool:
    """检查MinIO服务是否可用的便捷函数"""
    return minio_service.is_available()