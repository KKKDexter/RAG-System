# RAG-System

[![Python](https://img.shields.io/badge/Python-3.10-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green)](https://fastapi.tiangolo.com/)
[![Vue.js](https://img.shields.io/badge/Vue.js-3.x-green)](https://vuejs.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

一个基于大语言模型的检索增强生成(RAG)系统，支持文档管理、智能问答和大模型管理功能。系统采用前后端分离架构，支持本地存储和 MinIO 对象存储的灵活配置。

## ✨ 功能特性

### 📚 文档管理
- 支持多种文档格式：PDF、DOCX、DOC、TXT
- 智能存储策略：本地存储、MinIO 对象存储、双存储模式
- 按需目录创建，避免资源浪费
- 批量文档上传和管理

### 🤖 智能问答
- 基于 RAG 技术的文档检索增强生成
- 支持多种大语言模型（OpenAI、本地 Ollama 等）
- 向量化文档内容，高效语义检索
- 智能缓存机制，提升响应速度

### 🔧 系统管理
- 用户权限管理（管理员/普通用户）
- 大模型配置管理（Chat、Embedding、Rerank）
- 系统设置和日志监控
- RESTful API 设计

### 🗃️ 存储系统
- **本地存储**：适合开发环境，动态创建目录
- **MinIO 存储**：生产级对象存储，支持分布式部署
- **双存储模式**：数据冗余备份，自动故障转移

## 📋 技术栈

### 后端技术
- **框架**: FastAPI（Python 3.10）
- **数据库**: MySQL（关系型）+ Milvus（向量）+ Redis（缓存）
- **存储**: 本地文件系统 + MinIO 对象存储
- **AI 集成**: LangChain + OpenAI/Ollama

### 前端技术
- **框架**: Vue.js 3.x + Vite
- **UI 库**: Element Plus
- **状态管理**: Vuex/Pinia
- **构建工具**: Vite

## 🚀 快速开始

### 环境准备

#### 必要工具
- [Anaconda](https://www.anaconda.com/) 或 [Miniconda](https://docs.conda.io/en/latest/miniconda.html)
- [Node.js](https://nodejs.org/) (v14+) 和 npm
- [Git](https://git-scm.com/) (Windows 用户推荐使用 Git Bash)

#### 数据库服务
- **MySQL**: 存储用户信息、文档元数据
- **Milvus**: 存储文档向量数据
- **Redis**: 缓存查询结果
- **MinIO** (可选): 对象存储服务

### 1. 克隆项目

```bash
git clone <repository-url>
cd RAG-System
```

### 2. 后端环境配置

```bash
# 创建并激活 conda 环境
conda create -n rag-system python=3.10 -y
conda activate rag-system

# 安装 Python 依赖
cd backend
pip install -r requirements.txt
cd ..
```

### 3. 前端环境配置

```bash
cd frontend
npm install
cd ..
```

### 4. 环境变量配置

```bash
# 复制环境变量模板
cp .env.example .env
```

编辑 `.env` 文件，配置以下关键参数：

```env
# 数据库配置
DATABASE_URL=mysql+pymysql://root:password@localhost/rag_system
MILVUS_HOST=localhost
MILVUS_PORT=19530
REDIS_HOST=localhost
REDIS_PORT=6379

# 存储配置
STORAGE_MODE=local  # local, minio, both

# MinIO 配置（可选）
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_SECURE=False
MINIO_BUCKET_NAME=rag-documents

# 模型配置
CHAT_MODEL_API_KEY=your-api-key
EMBEDDING_MODEL_API_KEY=your-api-key
```

### 5. 启动服务

#### 启动后端服务
```bash
cd backend
python main.py --env dev --port 8000
```

#### 启动前端服务（新终端）
```bash
cd frontend
npm run dev
```

### 6. 访问应用

- **前端界面**: http://localhost:3000
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs

## 🗂️ 存储配置详解

### 存储模式对比

| 模式 | 描述 | 适用场景 | 目录创建 |
|------|------|----------|----------|
| `local` | 本地文件存储 | 开发环境、小规模部署 | 按需创建 `documents/` |
| `minio` | MinIO 对象存储 | 生产环境、分布式部署 | 不创建本地目录 |
| `both` | 双存储模式 | 高可用性、数据备份 | 创建本地目录 + MinIO |

### MinIO 部署指南

#### 使用 Docker 快速部署

```bash
# 在 Git Bash 中执行
docker run -d \
  --name minio \
  -p 9000:9000 \
  -p 9001:9001 \
  -e "MINIO_ACCESS_KEY=minioadmin" \
  -e "MINIO_SECRET_KEY=minioadmin" \
  quay.io/minio/minio server /data --console-address ":9001"
```

#### MinIO 管理控制台
- **地址**: http://localhost:9001
- **用户名**: minioadmin
- **密码**: minioadmin

### 存储模式配置

#### 本地存储模式
```env
STORAGE_MODE=local
```
- 文件保存在动态创建的 `documents/` 目录
- 适合开发和测试环境
- 无需额外服务依赖

#### MinIO 存储模式
```env
STORAGE_MODE=minio
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
```
- 文件保存在 MinIO 对象存储
- 支持分布式和高可用部署
- 不会创建本地目录

#### 双存储模式
```env
STORAGE_MODE=both
```
- 文件同时保存在本地和 MinIO
- 提供数据冗余和故障转移
- MinIO 不可用时自动降级到本地存储

## 📚 API 使用指南

### 文档上传

```bash
# 使用默认存储模式
curl -X POST "http://localhost:8000/v1/rag/upload" \
  -H "Authorization: Bearer your-token" \
  -F "file=@document.pdf"

# 指定存储模式
curl -X POST "http://localhost:8000/v1/rag/upload" \
  -H "Authorization: Bearer your-token" \
  -F "file=@document.pdf" \
  -F "storage_type=minio"
```

### 存储服务信息

```bash
curl -X GET "http://localhost:8000/v1/rag/storage-info" \
  -H "Authorization: Bearer your-token"
```

响应示例：
```json
{
  "storage_mode": "local",
  "minio_available": false,
  "supported_types": ["local", "minio", "both"]
}
```

## 🏗️ 项目架构

### 目录结构
```
RAG-System/
├── backend/                 # 后端服务
│   ├── api/                # API 路由
│   ├── module/             # 业务模块
│   │   ├── minio_service.py      # MinIO 服务
│   │   ├── storage_service.py    # 统一存储接口
│   │   ├── document_service.py   # 文档处理
│   │   └── ...
│   ├── config/             # 环境配置
│   └── main.py            # 服务入口
├── frontend/               # 前端应用
│   ├── src/
│   │   ├── views/         # 页面组件
│   │   ├── utils/         # 工具函数
│   │   └── ...
│   └── package.json
├── .env.example           # 环境变量模板
└── README.md             # 项目文档
```

## 🔍 故障排查

### 常见问题

#### MinIO 连接失败
1. 检查 `MINIO_ENDPOINT` 配置
2. 验证 MinIO 服务状态
3. 检查网络和防火墙设置
4. 确认访问密钥正确

#### 文件上传失败
1. 检查存储权限
2. 验证文件大小限制
3. 查看后端日志
4. 确认存储空间充足

## 🚀 部署指南

### 生产环境建议

1. **存储配置**
   ```env
   STORAGE_MODE=minio  # 或 both
   MINIO_SECURE=True
   ```

2. **安全设置**
   - 使用强密码配置 MinIO 访问密钥
   - 启用 HTTPS 和 SSL 证书
   - 配置防火墙和访问控制


**感谢使用 RAG-System！** 🎉