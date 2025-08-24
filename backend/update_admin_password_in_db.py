#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""直接更新RAG系统数据库中管理员密码的脚本"""

import os
import sys
import pymysql
from passlib.context import CryptContext

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_db_connection():
    """获取数据库连接"""
    # 这里使用默认的数据库连接信息
    # 在实际环境中，应该从.env文件或配置中读取
    try:
        connection = pymysql.connect(
            host='localhost',  # 数据库主机地址
            user='root',       # 数据库用户名
            password='',       # 数据库密码（如果有）
            database='rag_system',  # 数据库名
            cursorclass=pymysql.cursors.DictCursor
        )
        print("成功连接到数据库")
        return connection
    except Exception as e:
        print(f"数据库连接失败: {str(e)}")
        print("请检查数据库连接信息是否正确")
        sys.exit(1)

def update_admin_password(connection, password: str) -> bool:
    """更新管理员用户密码"""
    try:
        hashed_password = pwd_context.hash(password)
        print(f"生成的bcrypt哈希值: {hashed_password}")
        print(f"哈希值长度: {len(hashed_password)} 字符")
        
        with connection.cursor() as cursor:
            # 检查admin用户是否存在
            check_sql = "SELECT id, username FROM users WHERE username = 'admin'"
            cursor.execute(check_sql)
            user = cursor.fetchone()
            
            if not user:
                print("错误: 数据库中不存在admin用户")
                print("正在创建新的admin用户...")
                # 创建admin用户
                insert_sql = """
                INSERT INTO users (username, email, hashed_password, role) 
                VALUES ('admin', 'admin@example.com', %s, 'admin')
                """
                cursor.execute(insert_sql, (hashed_password,))
                connection.commit()
                print(f"成功创建admin用户，用户ID: {cursor.lastrowid}")
            else:
                # 更新现有admin用户的密码
                update_sql = """
                UPDATE users 
                SET hashed_password = %s 
                WHERE username = 'admin'
                """
                cursor.execute(update_sql, (hashed_password,))
                connection.commit()
                print(f"成功更新admin用户密码，用户ID: {user['id']}")
        
        return True
    except Exception as e:
        print(f"更新密码时出错: {str(e)}")
        connection.rollback()
        return False
    finally:
        connection.close()
        print("已关闭数据库连接")

def main():
    print("=====================================")
    print("=    RAG系统数据库管理员密码更新工具    =")
    print("=====================================")
    print("\n此工具用于直接连接数据库并更新管理员密码。")
    print("\n当前系统存在'bcrypt哈希格式错误'的问题，这可能是由于：")
    print("1. 数据库中存储的哈希值格式不正确")
    print("2. 哈希值可能已损坏")
    print("\n请输入新的管理员密码 (默认: admin123):")
    
    # 获取用户输入的密码，如果为空则使用默认密码
    password = input().strip()
    if not password:
        password = "admin123"
        print(f"\n未输入密码，使用默认密码: {password}")
    
    # 获取数据库连接并更新密码
    print("\n正在连接数据库...")
    connection = get_db_connection()
    
    print("\n正在更新管理员密码...")
    success = update_admin_password(connection, password)
    
    if success:
        print("\n=========================")
        print("= 管理员密码更新成功！  =")
        print("=========================")
        print(f"新密码: {password}")
        print("请使用此密码登录系统。")
        print("\n注意：为了安全起见，首次登录后请修改此默认密码。")
    else:
        print("\n管理员密码更新失败，请检查错误信息并重试。")

if __name__ == "__main__":
    main()