#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""用于重置RAG系统管理员密码的脚本"""

import os
import sys
from passlib.context import CryptContext

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def generate_password_hash(password: str) -> str:
    """生成密码的bcrypt哈希值"""
    return pwd_context.hash(password)

def print_password_update_sql(password: str) -> None:
    """生成更新管理员密码的SQL语句"""
    hashed_password = generate_password_hash(password)
    print(f"\n--- 生成的SQL更新语句 ---")
    print(f"UPDATE rag_system.users ")
    print(f"SET hashed_password = '{hashed_password}' ")
    print(f"WHERE username = 'admin';")
    print(f"\n--- 哈希值信息 ---")
    print(f"密码: {password}")
    print(f"哈希值长度: {len(hashed_password)} 字符")
    print(f"哈希值: {hashed_password}")
    print(f"\n请将上述SQL语句在数据库中执行，以更新管理员密码。")

def main():
    print("=====================================")
    print("=       RAG系统管理员密码重置工具      =")
    print("=====================================")
    print("\n此工具用于生成有效的bcrypt哈希值并提供更新数据库的SQL语句。")
    print("\n注意：当前系统中发现'bcrypt哈希格式错误'的问题，这可能是由于：")
    print("1. 数据库中存储的哈希值格式不正确")
    print("2. 哈希值可能已损坏")
    print("\n请输入新的管理员密码 (默认: admin123):")
    
    # 获取用户输入的密码，如果为空则使用默认密码
    password = input().strip()
    if not password:
        password = "admin123"
        print(f"\n未输入密码，使用默认密码: {password}")
    
    # 生成并显示SQL更新语句
    print_password_update_sql(password)
    
    # 提供额外的信息
    print(f"\n--- 问题分析 ---")
    print(f"1. 当前User模型中hashed_password字段长度为String(100)，这应该足够存储bcrypt哈希")
    print(f"2. 数据库初始化脚本中的哈希值可能格式不正确或已损坏")
    print(f"3. 执行上述SQL语句后，应该能够解决'bcrypt哈希格式错误'的问题")

if __name__ == "__main__":
    main()