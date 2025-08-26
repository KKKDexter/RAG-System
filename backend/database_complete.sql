-- ================================================================
-- RAG系统完整数据库初始化SQL脚本（已弃用）
-- ================================================================
-- 
-- ⚠️ 重要提示：此SQL脚本仅供文档参考，已被弃用！
-- 
-- 推荐使用方式：
--   python init_system_config.py
-- 
-- 此脚本合并了原有的 database_init.sql 和 add_system_config.sql
-- 包含完整的数据库结构定义，但实际使用中请使用 Python 初始化脚本
-- 
-- 优势对比：
-- - Python脚本：自动生成安全密钥、统一配置管理、错误处理完善
-- - SQL脚本：仅供理解数据库结构，缺乏动态配置生成能力
-- 
-- ================================================================

-- 创建数据库
CREATE DATABASE IF NOT EXISTS rag_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 使用数据库
USE rag_system;

-- ================================================================
-- 核心业务表定义
-- ================================================================

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
    hashed_password VARCHAR(255) NOT NULL COMMENT '密码哈希值，需要足够长度存储bcrypt结果',
    phone VARCHAR(20) NULL,
    role ENUM('admin', 'user') DEFAULT 'user',
    is_delete BOOLEAN DEFAULT FALSE COMMENT '逻辑删除标记',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_role (role),
    INDEX idx_is_delete (is_delete)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 文档表
CREATE TABLE IF NOT EXISTS documents (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    stored_path VARCHAR(255) NOT NULL,
    milvus_collection_name VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT '处理状态（pending,processing,processed,failed）',
    error_message VARCHAR(255) NULL COMMENT '错误信息',
    is_delete BOOLEAN DEFAULT FALSE COMMENT '逻辑删除标记',
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_user_id (user_id),
    INDEX idx_milvus_collection_name (milvus_collection_name),
    INDEX idx_document_status (status),
    INDEX idx_is_delete (is_delete),
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

-- ================================================================
-- 系统配置表定义（来自 add_system_config.sql）
-- ================================================================

-- 创建系统配置表
CREATE TABLE IF NOT EXISTS system_configs (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    config_key VARCHAR(100) NOT NULL UNIQUE COMMENT '配置键名',
    config_value TEXT COMMENT '配置值',
    config_type VARCHAR(20) DEFAULT 'string' COMMENT '配置值类型: string, integer, float, boolean',
    description VARCHAR(255) COMMENT '配置描述',
    is_sensitive BOOLEAN DEFAULT FALSE COMMENT '是否为敏感信息',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_config_key (config_key),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统配置表';

-- ================================================================
-- 初始数据插入
-- ================================================================

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

-- 插入初始的安全令牌配置数据
-- ⚠️ 注意：SECRET_KEY 在 SQL 脚本中无法安全生成！
-- 推荐使用 Python 脚本自动生成 32 字节安全密钥
INSERT INTO system_configs (config_key, config_value, config_type, description, is_sensitive, is_active) VALUES
('SECRET_KEY', 'UNSAFE-PLACEHOLDER-USE-PYTHON-SCRIPT', 'string', 'JWT密钥，用于生成和验证访问令牌（SQL脚本无法安全生成，请使用Python脚本）', TRUE, TRUE),
('ALGORITHM', 'HS256', 'string', 'JWT签名算法', FALSE, TRUE),
('ACCESS_TOKEN_EXPIRE_MINUTES', '30', 'integer', '访问令牌过期时间（分钟）', FALSE, TRUE)
ON DUPLICATE KEY UPDATE
    config_value = VALUES(config_value),
    description = VALUES(description),
    is_sensitive = VALUES(is_sensitive),
    is_active = VALUES(is_active),
    updated_at = CURRENT_TIMESTAMP;

-- ================================================================
-- 数据库优化设置
-- ================================================================

-- 设置全局字符集
SET GLOBAL character_set_server = 'utf8mb4';
SET GLOBAL collation_server = 'utf8mb4_unicode_ci';

-- ================================================================
-- 验证和输出信息
-- ================================================================

-- 显示创建结果
SHOW TABLES;

-- 验证用户表
SELECT COUNT(*) as total_users FROM users WHERE is_delete = FALSE;

-- 验证系统配置
SELECT 
    config_key,
    CASE 
        WHEN is_sensitive = TRUE THEN '***[敏感信息]***'
        ELSE config_value
    END as display_value,
    config_type,
    description,
    is_active,
    created_at
FROM system_configs
WHERE is_active = TRUE
ORDER BY config_key;

-- 显示配置统计
SELECT COUNT(*) as total_configs FROM system_configs WHERE is_active = TRUE;

-- ================================================================
-- 最终提示信息
-- ================================================================

SELECT '
⚠️ 重要提示：
1. 此 SQL 脚本仅供文档参考，已被弃用！
2. 推荐使用：python init_system_config.py
3. Python 脚本提供：
   - 自动生成 32 字节安全密钥
   - 完善的错误处理和日志记录
   - 与系统模型完全对齐的配置管理
4. 请确保在 .env 文件中配置正确的数据库连接信息
' AS important_notice;