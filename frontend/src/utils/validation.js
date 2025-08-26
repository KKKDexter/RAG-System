/**
 * 通用表单验证规则
 * 
 * 本文件定义了系统中常用的表单验证规则，避免重复定义
 * 
 * @author RAG-System Team
 * @version 1.0
 */

// ====================
// 基础验证规则
// ====================

/**
 * 用户名验证规则
 */
export const usernameRules = [
  { required: true, message: '请输入用户名', trigger: 'blur' },
  { min: 3, max: 50, message: '用户名长度在 3 到 50 个字符', trigger: 'blur' },
  { pattern: /^[a-zA-Z0-9_]+$/, message: '用户名只能包含字母、数字和下划线', trigger: 'blur' }
]

/**
 * 邮箱验证规则
 */
export const emailRules = [
  { required: true, message: '请输入邮箱', trigger: 'blur' },
  { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' },
  { max: 100, message: '邮箱长度不能超过100个字符', trigger: 'blur' }
]

/**
 * 密码验证规则
 */
export const passwordRules = [
  { required: true, message: '请输入密码', trigger: 'blur' },
  { min: 8, max: 50, message: '密码长度在 8 到 50 个字符', trigger: 'blur' },
  { pattern: /^(?=.*[a-zA-Z])(?=.*\d)/, message: '密码必须包含字母和数字', trigger: 'blur' }
]

/**
 * 简单密码验证规则（向后兼容）
 */
export const simplePasswordRules = [
  { required: true, message: '请输入密码', trigger: 'blur' },
  { min: 6, max: 20, message: '密码长度在 6 到 20 个字符', trigger: 'blur' }
]

/**
 * 手机号验证规则
 */
export const phoneRules = [
  { required: false, trigger: 'blur' },
  { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号码', trigger: 'blur' }
]

/**
 * 必填手机号验证规则
 */
export const requiredPhoneRules = [
  { required: true, message: '请输入手机号', trigger: 'blur' },
  { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号码', trigger: 'blur' }
]

// ====================
// API相关验证规则
// ====================

/**
 * API密钥验证规则
 */
export const apiKeyRules = [
  { required: true, message: '请输入API Key', trigger: 'blur' },
  { min: 10, message: 'API Key长度不能少于10个字符', trigger: 'blur' }
]

/**
 * URL验证规则
 */
export const urlRules = [
  { required: true, message: '请输入URL', trigger: 'blur' },
  { type: 'url', message: '请输入有效的URL', trigger: 'blur' }
]

/**
 * 模型名称验证规则
 */
export const modelNameRules = [
  { required: true, message: '请输入模型名称', trigger: 'blur' },
  { min: 1, max: 100, message: '模型名称长度在 1 到 100 个字符', trigger: 'blur' }
]

// ====================
// 系统配置验证规则
// ====================

/**
 * 温度参数验证规则
 */
export const temperatureRules = [
  { required: true, message: '请设置温度参数', trigger: 'blur' },
  { type: 'number', min: 0, max: 2, message: '温度参数应在0-2之间', trigger: 'blur' }
]

/**
 * 最大令牌数验证规则
 */
export const maxTokensRules = [
  { required: true, message: '请设置最大令牌数', trigger: 'blur' },
  { type: 'number', min: 1, max: 8192, message: '最大令牌数应在1-8192之间', trigger: 'blur' }
]

/**
 * 文件名验证规则
 */
export const filenameRules = [
  { required: true, message: '请输入文件名', trigger: 'blur' },
  { min: 1, max: 255, message: '文件名长度在 1 到 255 个字符', trigger: 'blur' },
  { pattern: /^[^<>:"/\\|?*]+$/, message: '文件名不能包含特殊字符', trigger: 'blur' }
]

// ====================
// 动态验证函数
// ====================

/**
 * 创建确认密码验证规则
 * @param {Object} form - 表单对象，需包含password字段
 * @returns {Array} 验证规则数组
 */
export const createConfirmPasswordRules = (form) => [
  { required: true, message: '请确认密码', trigger: 'blur' },
  {
    validator: (rule, value, callback) => {
      if (value !== form.password) {
        callback(new Error('两次输入的密码不一致'))
      } else {
        callback()
      }
    },
    trigger: 'blur'
  }
]

/**
 * 创建唯一性验证规则
 * @param {Function} checkUnique - 检查唯一性的异步函数
 * @param {string} fieldName - 字段名称
 * @returns {Array} 验证规则数组
 */
export const createUniqueRules = (checkUnique, fieldName) => [
  {
    validator: async (rule, value, callback) => {
      if (!value) {
        callback()
        return
      }
      try {
        const isUnique = await checkUnique(value)
        if (!isUnique) {
          callback(new Error(`该${fieldName}已存在`))
        } else {
          callback()
        }
      } catch (error) {
        callback(new Error(`验证${fieldName}唯一性时出错`))
      }
    },
    trigger: 'blur'
  }
]

// ====================
// 快捷组合规则
// ====================

/**
 * 用户创建表单验证规则
 */
export const userCreateFormRules = {
  username: usernameRules,
  email: emailRules,
  password: passwordRules,
  phone: phoneRules
}

/**
 * 登录表单验证规则
 */
export const loginFormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' }
  ]
}

/**
 * LLM模型配置验证规则
 */
export const llmModelRules = {
  name: modelNameRules,
  api_key: apiKeyRules,
  base_url: urlRules
}