#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移脚本 - 添加文档状态字段

这个脚本用于更新文档表，添加status和error_message字段
支持异步处理文档上传。

作者: RAG-System Team
版本: 1.0
"""

import os
import sys
from pathlib import Path
import pymysql
from dotenv import load_dotenv

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 加载.env文件
env_file = project_root / '.env'
load_dotenv(dotenv_path=env_file)

def migrate_documents_table():
    """
    修改documents表，添加status和error_message字段
    """
    print("[INFO] 开始迁移文档表，添加处理状态字段...")
    
    # 从.env文件读取数据库配置
    db_host = os.getenv('DB_HOST', 'localhost')
    db_user = os.getenv('DB_USER', 'root')
    db_pass = os.getenv('DB_PASS', '')
    db_name = os.getenv('DB_NAME', 'rag_system')
    db_port = int(os.getenv('DB_PORT', '3306'))
    
    print(f"[INFO] 连接到 MySQL 服务器: {db_user}@{db_host}:{db_port}/{db_name}")
    
    try:
        # 连接到MySQL数据库
        connection = pymysql.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_pass,
            database=db_name,
            charset='utf8mb4'
        )
        
        cursor = connection.cursor()
        
        # 检查status列是否已经存在
        cursor.execute("SHOW COLUMNS FROM documents LIKE 'status'")
        status_exists = cursor.fetchone() is not None
        
        # 检查error_message列是否已经存在
        cursor.execute("SHOW COLUMNS FROM documents LIKE 'error_message'")
        error_message_exists = cursor.fetchone() is not None
        
        # 添加status列
        if not status_exists:
            print("[INFO] 添加status列...")
            cursor.execute("""
                ALTER TABLE documents 
                ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'pending' 
                COMMENT '处理状态（pending,processing,processed,failed）' AFTER milvus_collection_name,
                ADD INDEX idx_document_status (status)
            """)
            print("[INFO] status列添加成功")
        else:
            print("[INFO] status列已存在，跳过")
        
        # 添加error_message列
        if not error_message_exists:
            print("[INFO] 添加error_message列...")
            cursor.execute("""
                ALTER TABLE documents 
                ADD COLUMN error_message VARCHAR(255) NULL 
                COMMENT '错误信息' AFTER status
            """)
            print("[INFO] error_message列添加成功")
        else:
            print("[INFO] error_message列已存在，跳过")
        
        # 更新现有记录的状态
        print("[INFO] 更新现有记录的处理状态...")
        cursor.execute("""
            UPDATE documents SET status = 'processed' 
            WHERE status = 'pending' OR status IS NULL
        """)
        updated_rows = cursor.rowcount
        print(f"[INFO] 已更新 {updated_rows} 条记录的状态为'processed'")
        
        # 提交事务
        connection.commit()
        print("[INFO] 文档表迁移成功完成")
        
    except Exception as e:
        print(f"[ERROR] 数据库迁移失败: {str(e)}")
        if 'connection' in locals():
            connection.rollback()
        sys.exit(1)
    finally:
        if 'connection' in locals() and connection.open:
            cursor.close()
            connection.close()
            print("[INFO] 数据库连接已关闭")

if __name__ == "__main__":
    migrate_documents_table()
    print("[INFO] 数据库迁移完成")