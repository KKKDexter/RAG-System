#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""用于重置RAG系统管理员密码的脚本

与系统认证服务完全对齐，支持数据库化的安全配置管理
"""

import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    # 导入系统模块
    from module.auth_service import get_password_hash, pwd_context
    from module.database import get_db_url
    from module.models import User
    from logger_config import get_logger
    
    logger = get_logger("reset_admin_password")
    HAS_DB_ACCESS = True
except Exception as e:
    print(f"警告: 无法导入系统模块: {e}")
    print("使用独立的bcrypt处理")
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    HAS_DB_ACCESS = False

def generate_password_hash_standalone(password: str) -> str:
    """独立的密码哈希生成（备用方案）"""
    return pwd_context.hash(password)

def generate_password_hash_integrated(password: str) -> str:
    """使用系统认证服务的密码哈希生成"""
    return get_password_hash(password)

def update_admin_password_direct(password: str) -> bool:
    """直接更新数据库中的管理员密码"""
    if not HAS_DB_ACCESS:
        return False
        
    try:
        # 获取数据库连接
        db_url = get_db_url()
        engine = create_engine(db_url)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        try:
            # 查找管理员用户
            admin_user = db.query(User).filter(
                User.username == 'admin',
                User.is_delete == False
            ).first()
            
            if not admin_user:
                logger.error("未找到admin用户")
                return False
            
            # 使用系统认证服务的密码哈希方法
            new_hashed_password = generate_password_hash_integrated(password)
            
            # 更新密码
            admin_user.hashed_password = new_hashed_password
            db.commit()
            
            logger.info(f"管理员密码更新成功，哈希长度: {len(new_hashed_password)}")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"更新密码失败: {e}")
            return False
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        return False

def print_password_update_sql(password: str) -> None:
    """生成更新管理员密码的SQL语句"""
    if HAS_DB_ACCESS:
        hashed_password = generate_password_hash_integrated(password)
        method_info = "使用系统认证服务的哈希方法"
    else:
        hashed_password = generate_password_hash_standalone(password)
        method_info = "使用独立的bcrypt哈希方法"
    
    print(f"\n--- 生成的SQL更新语句 ---")
    print(f"UPDATE rag_system.users ")
    print(f"SET hashed_password = '{hashed_password}' ")
    print(f"WHERE username = 'admin';")
    print(f"\n--- 哈希值信息 ---")
    print(f"密码: {password}")
    print(f"哈希方法: {method_info}")
    print(f"哈希值长度: {len(hashed_password)} 字符")
    print(f"哈希值: {hashed_password}")
    
    if HAS_DB_ACCESS:
        print(f"\n✅ 此哈希值与系统认证服务完全对齐")
    else:
        print(f"\n⚠️  警告: 未能导入系统模块，使用备用哈希方法")
    
    print(f"\n请将上述SQL语句在数据库中执行，以更新管理员密码。")

def main():
    print("=====================================")
    print("=       RAG系统管理员密码重置工具      =")
    print("=====================================")
    
    if HAS_DB_ACCESS:
        print("\n✅ 已成功连接系统模块，使用统一认证服务")
        print("支持数据库化安全配置管理")
    else:
        print("\n⚠️  警告: 未能连接系统模块，使用备用模式")
        
    print("\n请选择操作模式:")
    if HAS_DB_ACCESS:
        print("1. 直接更新数据库（推荐）")
    print("2. 生成SQL语句手动执行")
    
    try:
        if HAS_DB_ACCESS:
            choice = input("请输入选项 (1 或 2, 默认: 1): ").strip() or "1"
        else:
            choice = "2"
            print("自动选择选项 2: 生成SQL语句")
    except (EOFError, KeyboardInterrupt):
        print("\n操作已取消")
        return
    
    print("\n请输入新的管理员密码 (默认: admin123):")
    
    try:
        password = input().strip()
        if not password:
            password = "admin123"
            print(f"\n未输入密码，使用默认密码: {password}")
    except (EOFError, KeyboardInterrupt):
        print("\n操作已取消")
        return
    
    if choice == "1" and HAS_DB_ACCESS:
        print("\n正在直接更新数据库...")
        if update_admin_password_direct(password):
            print("\n✅ 管理员密码更新成功！")
            print("现在可以使用新密码登录系统")
        else:
            print("\n❌ 直接更新失败，转为生成SQL语句模式")
            print_password_update_sql(password)
    else:
        print_password_update_sql(password)
    
    print(f"\n--- 系统信息 ---")
    if HAS_DB_ACCESS:
        print(f"1. 使用系统统一认证服务，与登录模块完全对齐")
        print(f"2. 支持数据库化安全配置管理 (SECRET_KEY 从数据库动态获取)")
        print(f"3. 使用与 auth_service.py 相同的密码加密算法")
    else:
        print(f"1. 使用备用bcrypt加密方法")
        print(f"2. 建议配置正确的Python环境和数据库连接")
    
    print(f"4. 哈希值长度符合安全要求 (255字符字段长度)")

if __name__ == "__main__":
    main()