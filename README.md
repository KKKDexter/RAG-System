# RAG-System

一个基于大语言模型的检索增强生成(RAG)系统，支持文档管理、问答系统和大模型管理功能。

## 环境准备

### 前提条件
- Anaconda 或 Miniconda
- Node.js (v14+) 和 npm

### 1. 创建 Python 环境

```bash
# 创建 conda 环境
conda create -n rag-system python=3.10 -y

# 激活环境
conda activate rag-system

# 安装 Python 依赖
cd backend
pip install -r requirements.txt
cd ..
```

### 2. 安装前端依赖

```bash
cd frontend
npm install
cd ..
```

## 配置

### 1. 数据库配置

项目需要 MySQL、Milvus 和 Redis 数据库。请确保这些服务已安装并运行。

### 2. 环境变量配置

复制 `.env.example` 文件并重命名为 `.env`，然后根据您的环境修改配置：

```bash
cp .env.example .env
# 使用文本编辑器编辑 .env 文件
```

主要配置项：
- `DATABASE_URL`: MySQL 数据库连接字符串
- `MILVUS_HOST` 和 `MILVUS_PORT`: Milvus 向量数据库配置
- `REDIS_HOST` 和 `REDIS_PORT`: Redis 配置
- 模型 API 密钥配置

## 运行项目

### 1. 运行后端服务

```bash
cd backend
python main.py --env dev --port 8000
```

### 2. 运行前端服务

在另一个终端中执行：

```bash
cd frontend
npm run local
```

## 功能说明

1. **用户系统**: 支持用户注册、登录和权限管理
2. **文档管理**: 支持上传、查看和删除文档
3. **问答系统**: 基于 RAG 技术，利用文档内容回答问题
4. **大模型管理**: 支持添加、编辑和删除 chat、embedding 和 rerank 类型的大模型配置

## 注意事项

- 首次运行时，系统会自动创建数据库表
- 请确保您已正确配置数据库连接信息
- 对于使用 OpenAI 模型，需要提供有效的 API 密钥