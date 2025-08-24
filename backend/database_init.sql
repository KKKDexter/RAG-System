-- RAG系统数据库初始化SQL脚本
-- 创建数据库
CREATE DATABASE IF NOT EXISTS rag_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 使用数据库
USE rag_system;

-- 大模型配置表
CREATE TABLE IF NOT EXISTS llm_models (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    type ENUM('chat', 'embedding', 'rerank') NOT NULL,
    api_key VARCHAR(255) NULL,
    base_url VARCHAR(255) NULL,
    model_params TEXT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_delete BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_name (name),
    INDEX idx_type (type),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    hashed_password VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NULL,
    role ENUM('admin', 'user') DEFAULT 'user',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 文档表
CREATE TABLE IF NOT EXISTS documents (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    stored_path VARCHAR(255) NOT NULL,
    milvus_collection_name VARCHAR(100) NOT NULL,
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_milvus_collection_name (milvus_collection_name),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 问答历史表
CREATE TABLE IF NOT EXISTS qa_history (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    asked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建管理员用户（密码：admin123）
-- 注意：实际部署时应修改为安全密码
-- 以下是正确格式的bcrypt哈希值
INSERT INTO users (username, email, hashed_password, role) 
VALUES ('admin', 'admin@example.com', '$2b$12$DsEj8Rr5ZuC8FbEOTjgyZelF.pkGDvr2r3D72k2wC0kioPk1CzyPe', 'admin')
ON DUPLICATE KEY UPDATE 
    email = VALUES(email),
    hashed_password = VALUES(hashed_password),
    role = VALUES(role);

-- 插入示例大模型配置
INSERT INTO llm_models (name, type, api_key, base_url, model_params, is_active)
VALUES 
    ('gpt-3.5-turbo', 'chat', 'your-openai-api-key', 'https://api.openai.com/v1/chat/completions', '{"temperature": 0.7}', true),
    ('text-embedding-ada-002', 'embedding', 'your-openai-api-key', 'https://api.openai.com/v1/embeddings', '{"dimension": 1536}', true)
ON DUPLICATE KEY UPDATE 
    api_key = VALUES(api_key),
    base_url = VALUES(base_url),
    model_params = VALUES(model_params),
    is_active = VALUES(is_active);

-- 数据库优化设置
-- 设置全局字符集
SET GLOBAL character_set_server = 'utf8mb4';
SET GLOBAL collation_server = 'utf8mb4_unicode_ci';

-- 显示创建结果
SHOW TABLES;

-- 提示信息
SELECT '数据库初始化完成！请确保在.env文件中配置正确的数据库连接信息。' AS message;