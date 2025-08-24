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
  
  // 获取文档列表
  getDocuments(params) {
    return api.get('/v1/rag/documents', { params })
  },
  
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

export default api