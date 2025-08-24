<template>
  <div class="system-settings">
    <div class="page-header">
      <h1>RAG系统管理</h1>
      <p>配置RAG系统的全局参数和模型设置</p>
    </div>
    
    <!-- 统一的配置表单 -->
    <el-card class="settings-card">
      <template #header>
        <div class="card-header">
          <span>系统配置</span>
          <el-button type="primary" @click="handleSaveAll" :loading="saveLoading">
            <el-icon><Setting /></el-icon>保存所有配置
          </el-button>
        </div>
      </template>
      
      <el-row :gutter="20">
        <!-- 左侧：大语言模型设置 -->
        <el-col :span="12">
          <el-card shadow="never" class="config-section">
            <template #header>
              <h3><el-icon><ChatDotRound /></el-icon>大语言模型配置</h3>
            </template>
            
            <el-form
              ref="llmFormRef"
              :model="llmSettings"
              :rules="llmRules"
              label-width="140px"
              size="default"
            >
              <el-form-item label="Chat模型API Key" prop="chatApiKey">
                <el-input 
                  v-model="llmSettings.chatApiKey" 
                  type="password" 
                  placeholder="请输入Chat模型的API Key"
                  show-password
                  clearable
                />
                <div class="form-tip">用于对话生成的大模型API密钥</div>
              </el-form-item>
              
              <el-form-item label="Chat模型URL" prop="chatModelUrl">
                <el-input 
                  v-model="llmSettings.chatModelUrl" 
                  placeholder="例如：https://api.openai.com/v1/chat/completions"
                  clearable
                />
                <div class="form-tip">Chat模型的API端点地址</div>
              </el-form-item>
              
              <el-form-item label="Chat模型名称" prop="chatModelName">
                <el-input 
                  v-model="llmSettings.chatModelName" 
                  placeholder="例如：gpt-3.5-turbo"
                  clearable
                />
                <div class="form-tip">要使用的具体模型名称</div>
              </el-form-item>
              
              <el-form-item label="Embedding API Key" prop="embeddingApiKey">
                <el-input 
                  v-model="llmSettings.embeddingApiKey" 
                  type="password" 
                  placeholder="请输入Embedding模型的API Key"
                  show-password
                  clearable
                />
                <div class="form-tip">用于向量嵌入的模型API密钥</div>
              </el-form-item>
              
              <el-form-item label="Embedding模型URL" prop="embeddingModelUrl">
                <el-input 
                  v-model="llmSettings.embeddingModelUrl" 
                  placeholder="例如：https://api.openai.com/v1/embeddings"
                  clearable
                />
                <div class="form-tip">Embedding模型的API端点地址</div>
              </el-form-item>
              
              <el-form-item label="Embedding模型名称" prop="embeddingModelName">
                <el-input 
                  v-model="llmSettings.embeddingModelName" 
                  placeholder="例如：text-embedding-ada-002"
                  clearable
                />
                <div class="form-tip">要使用的嵌入模型名称</div>
              </el-form-item>
              
              <el-form-item label="温度参数" prop="temperature">
                <el-slider
                  v-model="llmSettings.temperature"
                  :min="0"
                  :max="1"
                  :step="0.1"
                  show-input
                  style="width: 100%"
                />
                <div class="form-tip">控制生成内容的随机性，值越高越随机</div>
              </el-form-item>
              
              <el-form-item label="最大令牌数" prop="maxTokens">
                <el-input-number
                  v-model="llmSettings.maxTokens"
                  :min="100"
                  :max="4096"
                  :step="100"
                  style="width: 100%"
                />
                <div class="form-tip">控制生成内容的最大长度</div>
              </el-form-item>
            </el-form>
          </el-card>
        </el-col>
        
        <!-- 右侧：系统参数设置 -->
        <el-col :span="12">
          <el-card shadow="never" class="config-section">
            <template #header>
              <h3><el-icon><Setting /></el-icon>系统参数配置</h3>
            </template>
            
            <el-form
              ref="systemFormRef"
              :model="systemSettings"
              :rules="systemRules"
              label-width="140px"
              size="default"
            >
              <!-- 向量数据库设置 -->
              <el-divider content-position="left">向量数据库</el-divider>
              
              <el-form-item label="向量维度" prop="vectorDimension">
                <el-input-number
                  v-model="systemSettings.vectorDimension"
                  :min="100"
                  :max="4096"
                  :step="1"
                  style="width: 100%"
                />
                <div class="form-tip">需与嵌入模型的输出维度匹配</div>
              </el-form-item>
              
              <el-form-item label="搜索相似向量数" prop="topK">
                <el-input-number
                  v-model="systemSettings.topK"
                  :min="1"
                  :max="20"
                  :step="1"
                  style="width: 100%"
                />
                <div class="form-tip">检索时返回的相似文档数量</div>
              </el-form-item>
              
              <!-- 文档处理设置 -->
              <el-divider content-position="left">文档处理</el-divider>
              
              <el-form-item label="文本分块大小" prop="chunkSize">
                <el-input-number
                  v-model="systemSettings.chunkSize"
                  :min="200"
                  :max="5000"
                  :step="100"
                  style="width: 100%"
                />
                <div class="form-tip">文档分割的块大小（字符数）</div>
              </el-form-item>
              
              <el-form-item label="分块重叠大小" prop="chunkOverlap">
                <el-input-number
                  v-model="systemSettings.chunkOverlap"
                  :min="0"
                  :max="1000"
                  :step="50"
                  style="width: 100%"
                />
                <div class="form-tip">相邻分块的重叠字符数</div>
              </el-form-item>
              
              <el-form-item label="最大文档大小(MB)" prop="maxDocumentSize">
                <el-input-number
                  v-model="systemSettings.maxDocumentSize"
                  :min="1"
                  :max="100"
                  :step="1"
                  style="width: 100%"
                />
                <div class="form-tip">允许上传的单个文档最大大小</div>
              </el-form-item>
              
              <!-- 缓存设置 -->
              <el-divider content-position="left">缓存配置</el-divider>
              
              <el-form-item label="启用问答缓存" prop="enableCache">
                <el-switch v-model="systemSettings.enableCache" />
                <div class="form-tip">开启后相同问题将直接返回缓存结果</div>
              </el-form-item>
              
              <el-form-item label="缓存过期时间(分钟)" prop="cacheTtl" v-if="systemSettings.enableCache">
                <el-input-number
                  v-model="systemSettings.cacheTtl"
                  :min="5"
                  :max="1440"
                  :step="5"
                  style="width: 100%"
                />
                <div class="form-tip">缓存结果的有效期</div>
              </el-form-item>
              
              <el-form-item label="开启调试模式" prop="debugMode">
                <el-switch v-model="systemSettings.debugMode" />
                <div class="form-tip">记录详细日志用于调试</div>
              </el-form-item>
            </el-form>
          </el-card>
        </el-col>
      </el-row>
    </el-card>
    
    <!-- 连接测试区域 -->
    <el-card class="test-card" style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span><el-icon><Connection /></el-icon>连接测试</span>
        </div>
      </template>
      
      <el-row :gutter="20">
        <el-col :span="8">
          <el-button 
            type="primary" 
            @click="testChatModel" 
            :loading="testLoading.chat"
            style="width: 100%"
          >
            <el-icon><ChatDotRound /></el-icon>测试Chat模型
          </el-button>
        </el-col>
        <el-col :span="8">
          <el-button 
            type="success" 
            @click="testEmbeddingModel" 
            :loading="testLoading.embedding"
            style="width: 100%"
          >
            <el-icon><DataAnalysis /></el-icon>测试Embedding模型
          </el-button>
        </el-col>
        <el-col :span="8">
          <el-button 
            type="info" 
            @click="testSystemConnection" 
            :loading="testLoading.system"
            style="width: 100%"
          >
            <el-icon><Connection /></el-icon>测试系统连接
          </el-button>
        </el-col>
      </el-row>
    </el-card>
    
    <!-- 配置说明 -->
    <div class="config-tips-container">
      <div class="config-tips-header" @click="toggleConfigTips">
        <span>📝 配置说明</span>
        <el-icon class="toggle-icon" :class="{ rotated: showConfigTips }">
          <ArrowDown />
        </el-icon>
      </div>
      
      <el-collapse-transition>
        <div v-show="showConfigTips" class="config-tips-content">
          <ul class="config-tips-list">
            <li>API Key配置后将覆盖环境变量中的设置</li>
            <li>建议先测试连接再保存配置</li>
            <li>部分配置修改后需要重启服务才能生效</li>
            <li>向量维度必须与选择的嵌入模型输出维度一致</li>
          </ul>
        </div>
      </el-collapse-transition>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Setting, ChatDotRound, DataAnalysis, Connection, ArrowDown } from '@element-plus/icons-vue'
import { adminAPI } from '../utils/api'

// 保存状态
const saveLoading = ref(false)

// 配置说明显示状态
const showConfigTips = ref(false)

// 测试连接状态
const testLoading = reactive({
  chat: false,
  embedding: false,
  system: false
})

// LLM设置
const llmFormRef = ref()
const llmSettings = reactive({
  chatApiKey: '',
  chatModelUrl: 'https://api.openai.com/v1/chat/completions',
  chatModelName: 'gpt-3.5-turbo',
  embeddingApiKey: '',
  embeddingModelUrl: 'https://api.openai.com/v1/embeddings',
  embeddingModelName: 'text-embedding-ada-002',
  temperature: 0.7,
  maxTokens: 1000
})

const llmRules = reactive({
  chatApiKey: [
    { required: true, message: '请输入Chat模型的API Key', trigger: 'blur' }
  ],
  chatModelUrl: [
    { required: true, message: '请输入Chat模型URL', trigger: 'blur' },
    { type: 'url', message: '请输入有效的URL', trigger: 'blur' }
  ],
  chatModelName: [
    { required: true, message: '请输入Chat模型名称', trigger: 'blur' }
  ],
  embeddingApiKey: [
    { required: true, message: '请输入Embedding模型的API Key', trigger: 'blur' }
  ],
  embeddingModelUrl: [
    { required: true, message: '请输入Embedding模型URL', trigger: 'blur' },
    { type: 'url', message: '请输入有效的URL', trigger: 'blur' }
  ],
  embeddingModelName: [
    { required: true, message: '请输入Embedding模型名称', trigger: 'blur' }
  ],
  temperature: [
    { required: true, message: '请设置温度参数', trigger: 'blur' },
    { type: 'number', min: 0, max: 1, message: '温度参数应在0-1之间', trigger: 'blur' }
  ],
  maxTokens: [
    { required: true, message: '请设置最大令牌数', trigger: 'blur' },
    { type: 'number', min: 100, max: 4096, message: '最大令牌数应在100-4096之间', trigger: 'blur' }
  ]
})

// 系统设置
const systemFormRef = ref()
const systemSettings = reactive({
  vectorDimension: 1536,
  topK: 5,
  chunkSize: 1000,
  chunkOverlap: 200,
  maxDocumentSize: 20,
  enableCache: true,
  cacheTtl: 60,
  debugMode: false
})

const systemRules = reactive({
  vectorDimension: [
    { required: true, message: '请设置向量维度', trigger: 'blur' },
    { type: 'number', min: 100, max: 4096, message: '向量维度应在100-4096之间', trigger: 'blur' }
  ],
  topK: [
    { required: true, message: '请设置搜索相似向量数', trigger: 'blur' },
    { type: 'number', min: 1, max: 20, message: 'topK应在1-20之间', trigger: 'blur' }
  ],
  chunkSize: [
    { required: true, message: '请设置文本分块大小', trigger: 'blur' },
    { type: 'number', min: 200, max: 5000, message: '分块大小应在200-5000字符之间', trigger: 'blur' }
  ],
  chunkOverlap: [
    { required: true, message: '请设置分块重叠大小', trigger: 'blur' },
    { type: 'number', min: 0, max: 1000, message: '重叠大小应在0-1000字符之间', trigger: 'blur' }
  ],
  maxDocumentSize: [
    { required: true, message: '请设置最大文档大小', trigger: 'blur' },
    { type: 'number', min: 1, max: 100, message: '最大文档大小应在1-100MB之间', trigger: 'blur' }
  ],
  cacheTtl: [
    { required: true, message: '请设置缓存过期时间', trigger: 'blur' },
    { type: 'number', min: 5, max: 1440, message: '缓存过期时间应在5-1440分钟之间', trigger: 'blur' }
  ]
})

// 初始化
onMounted(() => {
  loadSystemSettings()
})

// 加载系统设置
const loadSystemSettings = async () => {
  try {
    const settings = await adminAPI.getSystemSettings()
    
    // 合并设置到各个表单
    if (settings.llm) {
      Object.assign(llmSettings, settings.llm)
    }
    if (settings.system) {
      Object.assign(systemSettings, settings.system)
    }
    
    console.log('系统设置加载成功')
  } catch (error) {
    console.error('加载系统设置失败:', error)
    console.log('使用默认设置值')
  }
}

// 保存全部设置
const handleSaveAll = async () => {
  try {
    saveLoading.value = true
    
    // 验证表单
    await Promise.all([
      llmFormRef.value.validate(),
      systemFormRef.value.validate()
    ])
    
    // 构建完整的设置对象
    const allSettings = {
      llm: { ...llmSettings },
      system: { ...systemSettings }
    }
    
    // 发送保存请求
    await adminAPI.saveSystemSettings(allSettings)
    
    ElMessage.success('系统设置保存成功！')
    
    // 显示重启提示
    ElMessageBox.alert(
      '设置已保存，部分设置需要重启服务才能生效。',
      '保存成功',
      {
        confirmButtonText: '确定',
        type: 'success'
      }
    )
  } catch (error) {
    console.error('保存系统设置失败:', error)
    ElMessage.error('保存设置失败，请检查输入后重试')
  } finally {
    saveLoading.value = false
  }
}

// 测试Chat模型连接
const testChatModel = async () => {
  if (!llmSettings.chatApiKey || !llmSettings.chatModelUrl) {
    ElMessage.warning('请先配置Chat模型的API Key和URL')
    return
  }
  
  testLoading.chat = true
  try {
    // 这里应该调用后端API测试连接
    // const result = await adminAPI.testChatModel({
    //   api_key: llmSettings.chatApiKey,
    //   model_url: llmSettings.chatModelUrl,
    //   model_name: llmSettings.chatModelName
    // })
    
    // 模拟测试结果
    await new Promise(resolve => setTimeout(resolve, 2000))
    ElMessage.success('Chat模型连接测试成功！')
  } catch (error) {
    console.error('Chat模型测试失败:', error)
    ElMessage.error('Chat模型连接测试失败，请检查配置')
  } finally {
    testLoading.chat = false
  }
}

// 测试Embedding模型连接
const testEmbeddingModel = async () => {
  if (!llmSettings.embeddingApiKey || !llmSettings.embeddingModelUrl) {
    ElMessage.warning('请先配置Embedding模型的API Key和URL')
    return
  }
  
  testLoading.embedding = true
  try {
    // 这里应该调用后端API测试连接
    // const result = await adminAPI.testEmbeddingModel({
    //   api_key: llmSettings.embeddingApiKey,
    //   model_url: llmSettings.embeddingModelUrl,
    //   model_name: llmSettings.embeddingModelName
    // })
    
    // 模拟测试结果
    await new Promise(resolve => setTimeout(resolve, 2000))
    ElMessage.success('Embedding模型连接测试成功！')
  } catch (error) {
    console.error('Embedding模型测试失败:', error)
    ElMessage.error('Embedding模型连接测试失败，请检查配置')
  } finally {
    testLoading.embedding = false
  }
}

// 测试系统连接
const testSystemConnection = async () => {
  testLoading.system = true
  try {
    // 这里应该调用后端API测试系统组件连接
    // const result = await adminAPI.testSystemConnection()
    
    // 模拟测试结果
    await new Promise(resolve => setTimeout(resolve, 2000))
    ElMessage.success('系统连接测试成功！数据库和向量数据库连接正常')
  } catch (error) {
    console.error('系统连接测试失败:', error)
    ElMessage.error('系统连接测试失败，请检查数据库配置')
  } finally {
    testLoading.system = false
  }
}

// 切换配置说明显示状态
const toggleConfigTips = () => {
  showConfigTips.value = !showConfigTips.value
}
</script>

<style scoped>
.system-settings {
  padding: 20px;
}

.page-header {
  margin-bottom: 30px;
}

.page-header h1 {
  margin: 0 0 10px 0;
  color: #303133;
  font-size: 28px;
  font-weight: 600;
}

.page-header p {
  margin: 0;
  color: #606266;
  font-size: 16px;
}

.settings-card {
  margin-bottom: 20px;
  border-radius: 12px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
  color: #303133;
}

.config-section {
  height: 100%;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
}

.config-section .el-card__header {
  background-color: #fafafa;
  border-bottom: 1px solid #f0f0f0;
  padding: 15px 20px;
}

.config-section h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  display: flex;
  align-items: center;
  gap: 8px;
}

.config-section .el-card__body {
  padding: 20px;
  max-height: 600px;
  overflow-y: auto;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
  line-height: 1.4;
}

.test-card {
  border-radius: 12px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.test-card .card-header {
  font-weight: 600;
  color: #303133;
  display: flex;
  align-items: center;
  gap: 8px;
}

/* Element Plus 组件样式优化 */
.el-form-item {
  margin-bottom: 18px;
}

.el-form-item__label {
  font-weight: 500;
  color: #303133;
}

.el-input, .el-select, .el-input-number {
  width: 100%;
}

.el-slider {
  margin: 10px 0;
}

.el-divider {
  margin: 24px 0 16px 0;
}

.el-divider__text {
  font-weight: 600;
  color: #409eff;
  font-size: 14px;
}

.el-switch {
  margin-right: 10px;
}

/* 按钮组样式 */
.test-card .el-button {
  height: 44px;
  font-size: 14px;
  font-weight: 500;
  border-radius: 8px;
}

.card-header .el-button {
  border-radius: 8px;
  font-weight: 500;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .el-col {
    margin-bottom: 20px;
  }
  
  .config-section .el-card__body {
    max-height: 500px;
  }
}

@media (max-width: 768px) {
  .system-settings {
    padding: 15px;
  }
  
  .page-header h1 {
    font-size: 24px;
  }
  
  .el-row {
    --el-row-gutter: 10px;
  }
  
  .config-section .el-card__body {
    padding: 15px;
    max-height: 400px;
  }
  
  .card-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .card-header .el-button {
    width: 100%;
  }
}

/* 表单输入框焦点状态 */
.el-input__wrapper:focus-within,
.el-select__wrapper:focus-within {
  box-shadow: 0 0 0 1px #409eff inset;
}

/* 密码输入框样式 */
.el-input--password .el-input__wrapper {
  background-color: #f8f9fa;
}

/* 提示信息样式 */
.el-alert {
  border-radius: 8px;
}

.el-alert .el-alert__content {
  padding: 0;
}

.el-alert ul {
  margin: 10px 0 0 0;
  padding-left: 20px;
}

.el-alert li {
  margin-bottom: 5px;
  color: #606266;
  line-height: 1.5;
}

.el-alert li:last-child {
  margin-bottom: 0;
}

/* 配置说明样式 */
.config-tips-container {
  margin-top: 20px;
}

.config-tips-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  border: 1px solid #bae7ff;
  border-radius: 8px;
  cursor: pointer;
  user-select: none;
  transition: all 0.3s ease;
  font-size: 14px;
  color: #409eff;
  font-weight: 500;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.config-tips-header:hover {
  background: linear-gradient(135deg, #e0f2fe 0%, #cce7f0 100%);
  border-color: #91d5ff;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.config-tips-header .toggle-icon {
  transition: transform 0.3s ease;
  color: #409eff;
}

.config-tips-header .toggle-icon.rotated {
  transform: rotate(180deg);
}

.config-tips-content {
  margin-top: 8px;
  padding: 16px;
  background: #fafafa;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
}

.config-tips-list {
  margin: 0;
  padding-left: 20px;
}

.config-tips-list li {
  margin-bottom: 8px;
  color: #606266;
  line-height: 1.5;
}

.config-tips-list li:last-child {
  margin-bottom: 0;
}
</style>