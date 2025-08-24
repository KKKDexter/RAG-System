import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import router from '../router'

// 创建axios实例
const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 从localStorage获取token
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    // 对响应数据做处理
    return response.data
  },
  (error) => {
    // 处理响应错误
    if (error.response) {
      // 服务器返回错误状态码
      switch (error.response.status) {
        case 401:
          // 未授权，跳转到登录页
          ElMessageBox.alert('登录已过期，请重新登录', '提示', {
            confirmButtonText: '确定',
            callback: () => {
              localStorage.removeItem('token')
              localStorage.removeItem('userInfo')
              router.replace('/login')
            }
          })
          break
        case 403:
          // 权限不足
          ElMessage.error('权限不足，无法执行此操作')
          break
        case 404:
          // 请求的资源不存在
          ElMessage.error('请求的资源不存在')
          break
        case 500:
          // 服务器内部错误
          ElMessage.error('服务器内部错误，请稍后重试')
          break
        default:
          // 其他错误
          ElMessage.error(`请求失败: ${error.response.data.detail || error.response.statusText}`)
      }
    } else if (error.request) {
      // 请求已发送但没有收到响应
      ElMessage.error('网络连接超时，请检查网络设置')
    } else {
      // 请求配置出错
      ElMessage.error(`请求配置错误: ${error.message}`)
    }
    return Promise.reject(error)
  }
)

// 认证相关API
export const authAPI = {
  // 登录
  login(data) {
    return api.post('/v1/auth/login', data)
  },
  
  // 注册
  signup(data) {
    return api.post('/v1/auth/signup', data)
  },
  
  // 获取当前用户信息
  getCurrentUser() {
    return api.get('/v1/users/me')
  },
  
  // 刷新token
  refreshToken() {
    return api.post('/v1/auth/refresh')
  }
}

// RAG相关API
export const ragAPI = {
  // 上传文档
  uploadDocument(formData) {
    return api.post('/v1/rag/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },
  
<<<<<<< HEAD
  // 获取可用的embedding模型列表
  getEmbeddingModels() {
    return api.get('/v1/rag/embedding-models')
  },
  
=======
>>>>>>> main
  // 获取文档列表
  getDocuments(params) {
    return api.get('/v1/rag/documents', { params })
  },
  
<<<<<<< HEAD
  // 获取单个文档
  getDocument(id) {
    return api.get(`/v1/rag/documents/${id}`)
  },
  
  // 更新文档
  updateDocument(id, data) {
    return api.put(`/v1/rag/documents/${id}`, data)
  },
  
  // 更新文档文件
  updateDocumentFile(id, formData) {
    return api.put(`/v1/rag/documents/${id}/file`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },
  
=======
>>>>>>> main
  // 删除文档
  deleteDocument(id) {
    return api.delete(`/v1/rag/documents/${id}`)
  },
  
  // 提问
  askQuestion(data) {
    return api.post('/v1/rag/ask', data)
  },
  
  // 获取问答历史
  getQAHistory(params) {
    return api.get('/v1/rag/history', { params })
  }
}

// 管理员相关API
export const adminAPI = {
  // 获取所有用户
  getUsers(params) {
    return api.get('/v1/admin/users', { params })
  },
  
  // 创建用户
  createUser(data) {
    return api.post('/v1/admin/users', data)
  },
  
  // 更新用户
  updateUser(id, data) {
    return api.put(`/v1/admin/users/${id}`, data)
  },
  
  // 删除用户
  deleteUser(id) {
    return api.delete(`/v1/admin/users/${id}`)
  },
  
  // 获取系统设置
  getSystemSettings() {
    return api.get('/v1/admin/settings')
  },
  
  // 保存系统设置
  saveSystemSettings(data) {
    return api.post('/v1/admin/settings', data)
  },
  
  // 获取系统日志
  getSystemLogs(params) {
    return api.get('/v1/admin/logs', { params })
  }
}

<<<<<<< HEAD
=======
// 统计数据相关API
export const statsAPI = {
  // 获取仪表盘数据
  getDashboardStats() {
    return api.get('/v1/stats/dashboard')
  },
  
  // 获取文档统计
  getDocumentStats(params) {
    return api.get('/v1/stats/documents', { params })
  },
  
  // 获取问答统计
  getQAStats(params) {
    return api.get('/v1/stats/qa', { params })
  }
}

>>>>>>> main
// 大模型相关API
export const llmAPI = {
  // 创建大模型配置
  createModel(data) {
    return api.post('/llm/models', data)
  },
  
  // 获取大模型配置列表
  getModels(params) {
    return api.get('/llm/models', { params })
  },
  
  // 获取单个大模型配置
  getModel(id) {
    return api.get(`/llm/models/${id}`)
  },
  
  // 更新大模型配置
  updateModel(id, data) {
    return api.put(`/llm/models/${id}`, data)
  },
  
  // 删除大模型配置
  deleteModel(id) {
    return api.delete(`/llm/models/${id}`)
  },
  
  // 根据类型获取大模型配置
  getModelsByType(type) {
    return api.get(`/llm/models/type/${type}`)
  }
}

export default api