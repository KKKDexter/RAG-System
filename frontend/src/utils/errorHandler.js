/**
 * 前端通用错误处理工具
 * 
 * 本文件提供统一的错误处理函数和工具，避免重复的错误处理逻辑
 * 
 * @author RAG-System Team
 * @version 1.0
 */

import { ElMessage, ElMessageBox } from 'element-plus'

// ====================
// 通用错误处理函数
// ====================

/**
 * 处理API错误响应
 * @param {Error} error - 错误对象
 * @param {string} defaultMessage - 默认错误消息
 * @param {boolean} showDetail - 是否显示详细错误信息
 */
export const handleApiError = (error, defaultMessage = '操作失败', showDetail = false) => {
  console.error('API错误:', error)
  
  let message = defaultMessage
  
  if (error.response) {
    // 服务器响应错误
    const { status, data } = error.response
    
    switch (status) {
      case 400:
        message = data.detail || '请求参数错误'
        break
      case 401:
        message = '登录已过期，请重新登录'
        // 可以在这里添加跳转到登录页的逻辑
        localStorage.removeItem('token')
        localStorage.removeItem('userInfo')
        window.location.href = '/login'
        return
      case 403:
        message = '权限不足，无法执行此操作'
        break
      case 404:
        message = '请求的资源不存在'
        break
      case 409:
        message = data.detail || '数据冲突，资源已存在'
        break
      case 422:
        message = '数据验证失败'
        if (showDetail && data.detail) {
          message += ': ' + (Array.isArray(data.detail) ? data.detail.map(d => d.msg).join(', ') : data.detail)
        }
        break
      case 500:
        message = '服务器内部错误，请稍后重试'
        break
      default:
        message = data.detail || `请求失败 (${status})`
    }
  } else if (error.request) {
    // 网络错误
    message = '网络连接超时，请检查网络设置'
  } else {
    // 其他错误
    message = error.message || defaultMessage
  }
  
  ElMessage.error(message)
}

/**
 * 处理异步操作错误
 * @param {Function} asyncFn - 异步函数
 * @param {string} errorMessage - 错误消息
 * @param {boolean} showDetail - 是否显示详细错误
 * @returns {Function} 包装后的函数
 */
export const withErrorHandling = (asyncFn, errorMessage = '操作失败', showDetail = false) => {
  return async (...args) => {
    try {
      return await asyncFn(...args)
    } catch (error) {
      handleApiError(error, errorMessage, showDetail)
      throw error // 重新抛出错误，让调用者可以处理
    }
  }
}

/**
 * 处理表单提交错误
 * @param {Error} error - 错误对象
 * @param {string} operation - 操作名称
 */
export const handleFormError = (error, operation = '提交') => {
  if (error.response?.status === 422) {
    // 表单验证错误，显示详细信息
    handleApiError(error, `${operation}失败`, true)
  } else {
    handleApiError(error, `${operation}失败，请检查输入后重试`)
  }
}

// ====================
// 确认对话框工具
// ====================

/**
 * 显示删除确认对话框
 * @param {string} itemName - 要删除的项目名称
 * @param {string} itemType - 项目类型，如'用户'、'文档'等
 * @returns {Promise} 确认结果
 */
export const confirmDelete = (itemName, itemType = '项目') => {
  return ElMessageBox.confirm(
    `确定要删除${itemType}「${itemName}」吗？此操作不可恢复。`,
    '确认删除',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  )
}

/**
 * 显示通用确认对话框
 * @param {string} message - 确认消息
 * @param {string} title - 对话框标题
 * @param {string} confirmText - 确认按钮文本
 * @param {string} type - 对话框类型
 * @returns {Promise} 确认结果
 */
export const confirmAction = (message, title = '确认操作', confirmText = '确定', type = 'warning') => {
  return ElMessageBox.confirm(message, title, {
    confirmButtonText: confirmText,
    cancelButtonText: '取消',
    type
  })
}

// ====================
// 成功消息工具
// ====================

/**
 * 显示成功消息
 * @param {string} message - 成功消息
 */
export const showSuccess = (message) => {
  ElMessage.success(message)
}

/**
 * 显示警告消息
 * @param {string} message - 警告消息
 */
export const showWarning = (message) => {
  ElMessage.warning(message)
}

/**
 * 显示信息消息
 * @param {string} message - 信息消息
 */
export const showInfo = (message) => {
  ElMessage.info(message)
}

// ====================
// 批量操作工具
// ====================

/**
 * 处理批量操作
 * @param {Array} items - 要处理的项目数组
 * @param {Function} processor - 处理单个项目的函数
 * @param {string} operation - 操作名称
 * @param {Object} options - 选项
 * @returns {Promise} 处理结果
 */
export const handleBatchOperation = async (items, processor, operation = '处理', options = {}) => {
  const {
    showProgress = true,
    continueOnError = true,
    successMessage = null,
    errorMessage = null
  } = options
  
  const results = []
  const errors = []
  
  if (showProgress) {
    ElMessage.info(`开始${operation}，共 ${items.length} 项`)
  }
  
  for (let i = 0; i < items.length; i++) {
    try {
      const result = await processor(items[i], i)
      results.push(result)
    } catch (error) {
      errors.push({ item: items[i], error })
      if (!continueOnError) {
        break
      }
    }
  }
  
  // 显示结果消息
  if (errors.length === 0) {
    const message = successMessage || `${operation}完成，成功处理 ${results.length} 项`
    showSuccess(message)
  } else if (results.length === 0) {
    const message = errorMessage || `${operation}失败，所有项目都处理失败`
    ElMessage.error(message)
  } else {
    const message = `${operation}部分成功，成功 ${results.length} 项，失败 ${errors.length} 项`
    showWarning(message)
  }
  
  return { results, errors }
}

// ====================
// 表单验证辅助工具
// ====================

/**
 * 验证表单并处理错误
 * @param {Object} formRef - 表单引用
 * @param {string} operation - 操作名称
 * @returns {Promise<boolean>} 验证结果
 */
export const validateForm = async (formRef, operation = '提交') => {
  if (!formRef) {
    ElMessage.error('表单引用不存在')
    return false
  }
  
  try {
    await formRef.validate()
    return true
  } catch (error) {
    ElMessage.error(`${operation}失败，请检查表单输入`)
    return false
  }
}

/**
 * 重置表单
 * @param {Object} formRef - 表单引用
 * @param {Object} formData - 表单数据对象（可选）
 */
export const resetForm = (formRef, formData = null) => {
  if (formRef) {
    formRef.resetFields()
  }
  
  if (formData) {
    // 重置表单数据到初始状态
    Object.keys(formData).forEach(key => {
      if (typeof formData[key] === 'string') {
        formData[key] = ''
      } else if (typeof formData[key] === 'number') {
        formData[key] = 0
      } else if (typeof formData[key] === 'boolean') {
        formData[key] = false
      } else if (Array.isArray(formData[key])) {
        formData[key] = []
      } else if (typeof formData[key] === 'object' && formData[key] !== null) {
        formData[key] = {}
      } else {
        formData[key] = null
      }
    })
  }
}

// ====================
// 快捷操作组合
// ====================

/**
 * 执行带确认的删除操作
 * @param {string} itemName - 项目名称
 * @param {Function} deleteFunction - 删除函数
 * @param {string} itemType - 项目类型
 * @param {Function} onSuccess - 成功回调
 * @returns {Promise} 操作结果
 */
export const executeDelete = async (itemName, deleteFunction, itemType = '项目', onSuccess = null) => {
  try {
    await confirmDelete(itemName, itemType)
    await deleteFunction()
    showSuccess(`${itemType}删除成功`)
    if (onSuccess) {
      onSuccess()
    }
  } catch (error) {
    if (error !== 'cancel') {
      handleApiError(error, `删除${itemType}失败`)
    }
  }
}

/**
 * 执行表单提交操作
 * @param {Object} formRef - 表单引用
 * @param {Function} submitFunction - 提交函数
 * @param {string} operation - 操作名称
 * @param {Function} onSuccess - 成功回调
 * @returns {Promise} 操作结果
 */
export const executeSubmit = async (formRef, submitFunction, operation = '提交', onSuccess = null) => {
  try {
    const isValid = await validateForm(formRef, operation)
    if (!isValid) return
    
    await submitFunction()
    showSuccess(`${operation}成功`)
    if (onSuccess) {
      onSuccess()
    }
  } catch (error) {
    handleFormError(error, operation)
  }
}