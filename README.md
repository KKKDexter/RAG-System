# RAG系统项目

基于FastAPI和Vue 3构建的检索增强生成系统

## 项目结构
```
RAG/
├── backend/
│   ├── config/
│   │   └── dev.py       # 后端开发环境配置
│   ├── config.py        # 后端配置入口文件
│   └── ...
└── frontend/
    ├── config/
    │   └── dev.py       # 前端开发环境配置
    ├── vite.config.js   # 前端配置入口文件
    └── ...
```

## 配置管理

### 后端配置
后端配置位于`backend/config/`目录下，目前支持开发环境配置（dev.py）。

#### 使用方法
1. 在`backend/config/dev.py`中修改配置参数
2. 系统会自动从`backend/config.py`导入相应环境的配置

#### 配置参数说明
- `SECRET_KEY`: 安全密钥
- `ALGORITHM`: JWT算法
- `ACCESS_TOKEN_EXPIRE_MINUTES`: token过期时间
- `DATABASE_URL`: 数据库连接URL
- `MILVUS_HOST`: Milvus向量数据库主机
- `MILVUS_PORT`: Milvus向量数据库端口
- `REDIS_HOST`: Redis主机
- `REDIS_PORT`: Redis端口
- `REDIS_DB`: Redis数据库编号
- `CHUNK_SIZE`: 文档分块大小
- `CHUNK_OVERLAP`: 文档分块重叠大小
- `VECTOR_DIM`: 嵌入向量维度

### 前端配置
前端配置位于`frontend/config/`目录下，目前支持开发环境配置（dev.py）。

#### 使用方法
1. 在`frontend/config/dev.py`中修改配置参数
2. `vite.config.js`会自动导入相应环境的配置

#### 配置参数说明
- `server.port`: 开发服务器端口
- `server.proxy`: API代理配置
- `build.outDir`: 构建输出目录
- `build.sourcemap`: 是否生成sourcemap

## 切换环境
如需添加其他环境配置（如生产环境、测试环境）：
1. 在对应目录下创建新的配置文件（如`prod.py`）
2. 修改配置入口文件，根据环境变量导入相应的配置文件

## 部署说明
1. 启动Milvus、MySQL和Redis服务
2. 安装后端依赖: cd backend && pip install -r requirements.txt
3. 运行后端服务: uvicorn main:app --reload
4. 安装前端依赖: cd frontend && npm install
5. 运行前端服务: npm run dev