#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统配置初始化脚本
用于初始化系统配置数据到数据库中
"""

import os
import sys
import secrets
from pathlib import Path
import pymysql
from dotenv import load_dotenv

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 加载.env文件
env_file = project_root.parent / '.env'
load_dotenv(dotenv_path=env_file)

def create_database_if_not_exists():
    """
    直接连接MySQL，创建数据库（如果不存在）
    """
    print("[INFO] 检查并创建数据库...")
    
    # 从.env文件读取数据库配置
    db_host = os.getenv('DB_HOST', 'localhost')
    db_user = os.getenv('DB_USER', 'root')
    db_pass = os.getenv('DB_PASS', '')
    db_name = os.getenv('DB_NAME', 'rag_system')
    db_port = int(os.getenv('DB_PORT', '3306'))
    
    print(f"[INFO] 连接到 MySQL 服务器: {db_user}@{db_host}:{db_port}")
    
    try:
        # 连接到MySQL服务器（不指定数据库）
        connection = pymysql.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_pass,
            charset='utf8mb4'
        )
        
        cursor = connection.cursor()
        
        # 检查数据库是否存在
        cursor.execute(f"SHOW DATABASES LIKE '{db_name}'")
        result = cursor.fetchone()
        
        if result:
            print(f"[OK] 数据库 '{db_name}' 已存在")
        else:
            # 创建数据库
            cursor.execute(f"CREATE DATABASE {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print(f"[OK] 数据库 '{db_name}' 创建成功")
        
        cursor.close()
        connection.close()
        
        return True
        
    except Exception as e:
        print(f"[ERROR] 数据库创建失败: {e}")
        return False

from sqlalchemy.orm import Session
from module.database import get_db, engine
from module.models import Base, SystemConfig, ConfigType, User, Role
from module.config_manager import config_manager, generate_secret_key
import bcrypt

def create_tables():
    """创建数据库表（包括系统配置表）"""
    print("正在创建数据库表...")
    try:
        # 创建所有表（包括 SystemConfig）
        Base.metadata.create_all(bind=engine)
        print("[OK] 数据库表创建完成（包括 system_configs 表）")
        
        # 验证 system_configs 表是否创建成功
        db = next(get_db())
        try:
            # 尝试查询 system_configs 表
            db.execute("SELECT COUNT(*) FROM system_configs")
            print("[OK] system_configs 表验证成功")
            
            # 检查 documents 表的字段结构，确保包含最新字段
            try:
                db.execute("SELECT status, error_message FROM documents LIMIT 1")
                print("[OK] documents 表字段验证成功（包含 status 和 error_message）")
            except Exception as e:
                print(f"[WARNING] documents 表可能缺少新字段: {e}")
                print("[INFO] 如果遇到字段缺失错误，请运行: python migrate_documents.py")
                
        except Exception as e:
            print(f"[WARNING] system_configs 表验证失败: {e}")
        finally:
            db.close()
            
    except Exception as e:
        print(f"[ERROR] 创建数据库表失败: {e}")
        raise

def create_default_admin():
    """创建默认管理员用户（替代 database_init.sql 中的用户创建）"""
    print("\n=== 创建默认管理员用户 ===")
    
    db: Session = next(get_db())
    
    try:
        # 检查是否已存在管理员用户
        existing_admin = db.query(User).filter(
            User.username == "admin",
            User.role == Role.admin
        ).first()
        
        if existing_admin:
            print("[OK] 管理员用户已存在，跳过创建")
            return True
        
        # 创建默认管理员用户
        password = "admin123"
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        admin_user = User(
            username="admin",
            email="admin@rag-system.com",
            hashed_password=hashed_password,
            phone="",
            role=Role.admin,
            is_delete=False
        )
        
        db.add(admin_user)
        db.commit()
        
        print("[OK] 默认管理员用户创建成功")
        print("[INFO] 用户名: admin")
        print("[INFO] 密码: admin123")
        print("[WARNING] 请在首次登录后立即修改密码！")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] 创建管理员用户失败: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def init_system_configs():
    """初始化系统配置"""
    db: Session = next(get_db())
    
    try:
        # 定义初始配置数据（仅安全令牌配置）
        # 自动生成安全的 SECRET_KEY
        generated_secret_key = generate_secret_key()
        print(f"[OK] 已生成安全密钥（长度: {len(generated_secret_key)} 字符）")
        
        initial_configs = [
            {
                'config_key': 'SECRET_KEY',
                'config_value': generated_secret_key,
                'config_type': ConfigType.string,
                'description': 'JWT密钥，用于生成和验证访问令牌（自动生成）',
                'is_sensitive': True
            },
            {
                'config_key': 'ALGORITHM',
                'config_value': 'HS256',
                'config_type': ConfigType.string,
                'description': 'JWT签名算法',
                'is_sensitive': False
            },
            {
                'config_key': 'ACCESS_TOKEN_EXPIRE_MINUTES',
                'config_value': '30',
                'config_type': ConfigType.integer,
                'description': 'JWT访问令牌过期时间（分钟），用于控制用户登录会话的安全性',
                'is_sensitive': False
            }
        ]
        
        print("正在初始化系统配置...")
        
        for config_data in initial_configs:
            # 检查配置是否已存在
            existing_config = db.query(SystemConfig).filter(
                SystemConfig.config_key == config_data['config_key']
            ).first()
            
            if existing_config:
                print(f"配置 {config_data['config_key']} 已存在，跳过")
                continue
            
            # 创建新配置
            new_config = SystemConfig(
                config_key=config_data['config_key'],
                config_value=config_data['config_value'],
                config_type=config_data['config_type'],
                description=config_data['description'],
                is_sensitive=config_data['is_sensitive'],
                is_active=True
            )
            
            db.add(new_config)
            print(f"添加配置: {config_data['config_key']}")
        
        db.commit()
        print("系统配置初始化完成")
        
        # 显示已添加的配置
        configs = db.query(SystemConfig).filter(SystemConfig.is_active == True).all()
        print(f"\n当前活跃配置项（共 {len(configs)} 个）：")
        for config in configs:
            sensitive_mark = " [敏感]" if config.is_sensitive else ""
            print(f"  {config.config_key}: {config.config_value}{sensitive_mark}")
        
    except Exception as e:
        print(f"初始化配置时发生错误: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def migrate_env_configs():
    """从环境变量迁移配置（仅作为初始化时的一次性迁移）"""
    print("\n=== 检查环境变量配置迁移 ===")
    
    # 检查 .env 文件
    env_file = project_root / '.env'
    if env_file.exists():
        print(f"发现 .env 文件: {env_file}")
        
        print("[INFO] 安全令牌配置已完全数据库化，不再从 .env 文件读取")
        print("[INFO] SECRET_KEY、ALGORITHM、ACCESS_TOKEN_EXPIRE_MINUTES 已自动生成并存储在数据库中")
        
        print("\n[INFO] 重要提示：")
        print("   - 安全配置现在完全存储在数据库中")
        print("   - .env 文件中的 SECRET_KEY 等配置将不再被读取")
        print("   - 请通过 /v1/config/ API 管理这些配置")
        print("   - .env 文件仅用于数据库连接和其他非安全配置")
        
    else:
        print("[INFO] 未发现 .env 文件，所有安全配置将使用数据库中的值")

def main():
    """主函数 - 统一初始化数据库和系统配置"""
    print("=== RAG 系统初始化脚本 ===")
    print("[INFO] 此脚本将替代 database_init.sql 和 add_system_config.sql")
    print("[INFO] 统一通过 Python 服务初始化所有组件\n")
    
    try:
        # 0. 检查并创建数据库（如果不存在）
        if not create_database_if_not_exists():
            print("[ERROR] 数据库创建失败，无法继续初始化")
            sys.exit(1)
        
        # 1. 创建数据库表（替代 database_init.sql 和 add_system_config.sql）
        create_tables()
        
        # 2. 创建默认管理员用户（替代 database_init.sql）
        create_default_admin()
        
        # 3. 初始化安全令牌配置
        init_system_configs()
        
        # 4. 检查环境变量配置状态
        migrate_env_configs()
        
        print("\n[OK] RAG 系统初始化成功！")
        print("\n[INFO] 现在您可以：")
        print("1. 启动后端服务: python main_fixed.py --env dev --port 8000")
        print("2. 通过 API 接口管理系统配置: /v1/config/")
        print("3. 系统完全依赖数据库中的安全令牌配置")
        print("4. 数据库连接配置仍从 .env 文件读取")
        
        print("\n[INFO] 安全令牌配置说明：")
        print("- SECRET_KEY: JWT 加密密钥")
        print("- ALGORITHM: JWT 签名算法")
        print("- ACCESS_TOKEN_EXPIRE_MINUTES: 用户登录会话过期时间（分钟）")
        
    except Exception as e:
        print(f"\n[ERROR] 初始化失败: {e}")
        print("\n[INFO] 请检查：")
        print("1. 数据库服务是否正常运行")
        print("2. .env 文件中的数据库连接配置")
        print("3. 数据库用户权限")
        sys.exit(1)

if __name__ == "__main__":
    main()