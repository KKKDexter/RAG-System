<template>
  <div class="qa-system">
    <div class="page-header">
      <h1>问答系统</h1>
      <p>向您的知识库提问，获取智能回答</p>
    </div>
    
    <!-- 会话区域 -->
    <div class="chat-container">
      <!-- 聊天消息列表 -->
      <div class="chat-messages" ref="chatMessagesRef">
        <div v-if="messages.length === 0" class="empty-chat">
          <el-empty description="还没有聊天记录，开始提问吧！" />
        </div>
        
        <div v-for="(message, index) in messages" :key="index" class="message-wrapper">
          <!-- 用户消息 -->
          <div v-if="message.role === 'user'" class="message user-message">
            <div class="message-avatar">
              <el-avatar>{{ userInfo?.username?.charAt(0).toUpperCase() }}</el-avatar>
            </div>
            <div class="message-content">
              <div class="message-text">{{ message.content }}</div>
              <div class="message-time">{{ message.time }}</div>
            </div>
          </div>
          
          <!-- 系统消息 -->
          <div v-else class="message system-message">
            <div class="message-avatar">
              <el-avatar icon="Bot" />
            </div>
            <div class="message-content">
              <div class="message-text">{{ message.content }}</div>
              <div class="message-time">{{ message.time }}</div>
            </div>
          </div>
        </div>
        
        <!-- 加载状态 -->
        <div v-if="isLoading" class="loading-message">
          <el-icon class="is-loading"><Loading /></el-icon>
          <span>正在生成回答...</span>
        </div>
      </div>
      
      <!-- 输入区域 -->
      <div class="chat-input-area">
        <h3 style="margin: 0 0 10px 0; color: #409eff;">💬 在这里输入您的问题：</h3>
        <!-- 使用原生textarea替代el-textarea -->
        <textarea
          v-model="currentQuestion"
          placeholder="请输入您的问题..."
          rows="4"
          maxlength="1000"
          style="width: 100%; padding: 12px; border: 2px solid #409eff; border-radius: 8px; font-size: 14px; resize: none; font-family: inherit; box-sizing: border-box;"
          @input="handleInput"
          @keydown.enter.exact="handleAskQuestion"
          @keydown.enter.shift="handleNewLine"
        ></textarea>
        <div style="text-align: right; margin-top: 5px; color: #999; font-size: 12px;">
          {{ currentQuestion.length }}/1000
        </div>
        
        <div class="input-actions">
          <el-button type="primary" @click="handleAskQuestion" :loading="isLoading" :disabled="!currentQuestion.trim()">
            <el-icon><Message /></el-icon>发送
          </el-button>
          <el-button @click="clearChat" v-if="messages.length > 0">
            <el-icon><Delete /></el-icon>清空
          </el-button>
        </div>
      </div>
    </div>
    
    <!-- 提示信息 -->
    <el-card class="tips-card">
      <template #header>
        <div class="card-header">
          <span>使用提示</span>
        </div>
      </template>
      <ul class="tips-list">
        <li>1. 确保您已上传相关文档到知识库</li>
        <li>2. 提问越具体，得到的回答越准确</li>
        <li>3. 您可以基于之前的回答继续提问</li>
        <li>4. Shift + Enter 可以输入换行符</li>
      </ul>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Message, Delete, Loading } from '@element-plus/icons-vue'
import { ragAPI } from '../utils/api.js'

// 用户信息
const userInfo = ref(null)

// 聊天相关
const currentQuestion = ref('')
const messages = ref([])
const isLoading = ref(false)
const chatMessagesRef = ref()

// 初始化
onMounted(() => {
  console.log('QASystem组件已加载');
  console.log('currentQuestion初始值:', currentQuestion.value);
  
  // 从本地存储获取用户信息
  const storedUserInfo = localStorage.getItem('userInfo')
  if (storedUserInfo) {
    userInfo.value = JSON.parse(storedUserInfo)
    console.log('用户信息:', userInfo.value);
  }
  
  // 可以从本地存储加载历史聊天记录（如果实现了的话）
  // loadChatHistory()
})

// 处理提问
const handleAskQuestion = async () => {
  const question = currentQuestion.value.trim()
  if (!question) {
    ElMessage.warning('请输入问题')
    return
  }
  
  // 添加用户消息到聊天列表
  const now = new Date()
  const timeString = now.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit'
  })
  
  messages.value.push({
    role: 'user',
    content: question,
    time: timeString
  })
  
  // 清空输入框
  currentQuestion.value = ''
  
  // 滚动到底部
  await nextTick()
  scrollToBottom()
  
  try {
    isLoading.value = true
    
    // 发送提问请求
    const response = await ragAPI.askQuestion({
      question: question
    })
    
    // 添加系统回答到聊天列表
    const answerTime = new Date().toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit'
    })
    
    messages.value.push({
      role: 'system',
      content: response.answer,
      time: answerTime,
      // 这里可以根据实际API返回添加参考文档信息
      // references: response.references || []
    })
    
    // 滚动到底部
    await nextTick()
    scrollToBottom()
    
  } catch (error) {
    console.error('提问失败:', error)
    messages.value.push({
      role: 'system',
      content: '抱歉，处理您的问题时出错了，请稍后重试。',
      time: new Date().toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit'
      })
    })
    // 错误处理已在api.ts中完成
  } finally {
    isLoading.value = false
    
    // 滚动到底部
    await nextTick()
    scrollToBottom()
  }
}

// 处理输入
const handleInput = (event) => {
  // 确保输入内容被正确更新
  currentQuestion.value = event.target.value
  console.log('输入事件触发:', currentQuestion.value);
  console.log('事件对象:', event);
}

// 处理换行
const handleNewLine = (event) => {
  // 允许Shift + Enter添加换行
  event.preventDefault()
  const textarea = event.target
  const start = textarea.selectionStart
  const end = textarea.selectionEnd
  const value = currentQuestion.value
  currentQuestion.value = value.substring(0, start) + '\n' + value.substring(end)
  
  // 设置光标位置
  setTimeout(() => {
    textarea.selectionStart = textarea.selectionEnd = start + 1
  }, 0)
}

// 清空聊天
const clearChat = () => {
  ElMessageBox.confirm(
    '确定要清空所有聊天记录吗？',
    '确认清空',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  )
    .then(() => {
      messages.value = []
      ElMessage.success('聊天记录已清空')
    })
    .catch(() => {
      ElMessage.info('已取消清空')
    })
}

// 滚动到底部
const scrollToBottom = () => {
  if (chatMessagesRef.value) {
    chatMessagesRef.value.scrollTop = chatMessagesRef.value.scrollHeight
  }
}

// 加载聊天历史记录（可选实现）
const loadChatHistory = () => {
  // 从本地存储或API加载历史记录
  // 这里仅作为示例，实际项目中可能需要从服务器获取
  try {
    const history = localStorage.getItem('chatHistory')
    if (history) {
      messages.value = JSON.parse(history)
    }
  } catch (error) {
    console.error('加载聊天历史失败:', error)
  }
}

// 保存聊天历史记录（可选实现）
const saveChatHistory = () => {
  // 保存到本地存储
  try {
    localStorage.setItem('chatHistory', JSON.stringify(messages.value))
  } catch (error) {
    console.error('保存聊天历史失败:', error)
  }
}
</script>

<style scoped>
.qa-system {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0 0 10px 0;
  color: #333;
}

.page-header p {
  margin: 0;
  color: #666;
}

/* 聊天容器样式 */
.chat-container {
  display: flex;
  flex-direction: column;
  height: 600px; /* 固定高度 */
  min-height: 400px;
  border: 1px solid #e1e5e9;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 20px;
  background: white;
}

/* 为小屏幕调整聊天容器高度 */
@media (max-width: 768px) {
  .chat-container {
    height: calc(100vh - 320px);
  }
}

/* 聊天消息列表样式 */
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background-color: #f8f9fa;
}

.empty-chat {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #909399;
}

/* 消息样式 */
.message-wrapper {
  margin-bottom: 20px;
}

.message {
  display: flex;
  align-items: flex-start;
}

.user-message {
  flex-direction: row-reverse;
}

.system-message {
  flex-direction: row;
}

.message-avatar {
  margin: 0 10px;
  flex-shrink: 0;
}

.message-content {
  max-width: 70%;
}

.user-message .message-content {
  text-align: right;
}

.system-message .message-content {
  text-align: left;
}

.message-text {
  padding: 10px 15px;
  border-radius: 10px;
  word-wrap: break-word;
  line-height: 1.5;
}

.user-message .message-text {
  background-color: #409eff;
  color: white;
}

.system-message .message-text {
  background-color: white;
  color: #333;
  border: 1px solid #e1e5e9;
}

.message-time {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}

/* 加载消息样式 */
.loading-message {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  color: #909399;
}

.loading-message .el-icon {
  margin-right: 10px;
}

/* 输入区域样式 */
.chat-input-area {
  padding: 20px;
  border-top: 1px solid #e1e5e9;
  background: white;
  flex-shrink: 0;
  min-height: 120px;
}

.input-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

/* 提示卡片样式 */
.tips-card {
  background-color: #f0f9ff;
  border-color: #bae7ff;
}

.tips-list {
  margin: 0;
  padding-left: 20px;
}

.tips-list li {
  margin-bottom: 5px;
  color: #666;
}

.tips-list li:last-child {
  margin-bottom: 0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .chat-container {
    height: calc(100vh - 320px);
  }
  
  .message-content {
    max-width: 85%;
  }
  
  .input-actions {
    flex-direction: column;
  }
  
  .input-actions .el-button {
    width: 100%;
  }
}
</style>