<template>
  <div class="login-container">
    <div class="login-form-wrapper">
      <div class="login-header">
        <h2>RAG系统登录</h2>
        <p>欢迎使用检索增强生成系统</p>
      </div>
      
      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="loginRules"
        label-position="left"
        label-width="80px"
        class="login-form"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="请输入用户名"
            prefix-icon="User"
            autocomplete="username"
          />
        </el-form-item>
        
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入密码"
            prefix-icon="Lock"
            autocomplete="current-password"
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        
        <el-form-item>
          <el-checkbox v-model="rememberMe">记住密码</el-checkbox>
          <el-link type="primary" style="float: right;">忘记密码？</el-link>
        </el-form-item>
        
        <el-form-item>
          <el-button
            type="primary"
            :loading="isLoading"
            class="login-button"
            @click="handleLogin"
          >
            登录
          </el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElForm } from 'element-plus'
import { authAPI } from '../utils/api'

const router = useRouter()
const loginFormRef = ref()
const isLoading = ref(false)
const rememberMe = ref(false)

// 登录表单数据
const loginForm = reactive({
  username: '',
  password: ''
})

// 表单验证规则
const loginRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度在 6 到 20 个字符', trigger: 'blur' }
  ]
}

// 处理登录
const handleLogin = async () => {
  // 验证表单
  if (!loginFormRef.value) return
  
  try {
    await loginFormRef.value.validate()
    isLoading.value = true
    
    // 发送登录请求使用authAPI
    const response = await authAPI.login(loginForm)
    
    // 保存token和token_type
    localStorage.setItem('token', response.access_token)
    localStorage.setItem('token_type', response.token_type)
    
    // 获取用户信息
    const userResponse = await authAPI.getCurrentUser()
    localStorage.setItem('userInfo', JSON.stringify(userResponse))
    
    // 记住密码处理
    if (rememberMe.value) {
      localStorage.setItem('rememberedUsername', loginForm.username)
    } else {
      localStorage.removeItem('rememberedUsername')
    }
    
    ElMessage.success('登录成功')
    router.push({ name: 'Dashboard' })
  } catch (error) {
    console.error('登录失败:', error)
    // 错误处理已在api.ts中完成
  } finally {
    isLoading.value = false
  }
}

// 初始化页面，检查是否有记住的用户名
onMounted(() => {
  const rememberedUsername = localStorage.getItem('rememberedUsername')
  if (rememberedUsername) {
    loginForm.username = rememberedUsername
    rememberMe.value = true
  }
})
</script>

<style scoped>
.login-container {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-form-wrapper {
  background: white;
  padding: 40px;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 400px;
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.login-header h2 {
  margin: 0 0 10px 0;
  color: #333;
}

.login-header p {
  margin: 0;
  color: #666;
  font-size: 14px;
}

.login-form {
  width: 100%;
}

.login-button {
  width: 100%;
  height: 40px;
  font-size: 16px;
}

/* 表单项间距 */
.el-form-item {
  margin-bottom: 20px;
}
</style>