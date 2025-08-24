<template>
  <div class="system-settings">
    <div class="page-header">
      <h1>系统设置</h1>
      <p>管理RAG系统的全局配置参数</p>
    </div>
    
    <el-steps :active="activeStep" finish-status="success" style="margin-bottom: 30px">
      <el-step title="LLM设置" />
      <el-step title="向量数据库设置" />
      <el-step title="缓存设置" />
      <el-step title="系统优化" />
    </el-steps>
    
    <el-card>
      <template #header>
        <div class="card-header">
          <span v-if="activeStep === 0">大语言模型设置</span>
          <span v-else-if="activeStep === 1">Milvus向量数据库设置</span>
          <span v-else-if="activeStep === 2">Redis缓存设置</span>
          <span v-else-if="activeStep === 3">系统优化设置</span>
        </div>
      </template>
      
      <!-- LLM设置 -->
      <div v-if="activeStep === 0">
        <el-form
          ref="llmFormRef"
          :model="llmSettings"
          :rules="llmRules"
          label-width="150px"
          style="margin-top: 20px"
        >
          <el-form-item label="默认模型" prop="defaultModel">
            <el-select v-model="llmSettings.defaultModel" placeholder="请选择默认模型">
              <el-option label="gpt-3.5-turbo" value="gpt-3.5-turbo" />
              <el-option label="gpt-4" value="gpt-4" />
              <el-option label="claude-3-opus" value="claude-3-opus" />
              <el-option label="claude-3-sonnet" value="claude-3-sonnet" />
              <el-option label="gemini-pro" value="gemini-pro" />
            </el-select>
          </el-form-item>
          
          <el-form-item label="温度参数" prop="temperature">
            <el-slider
              v-model="llmSettings.temperature"
              :min="0"
              :max="1"
              :step="0.1"
              show-input
            />
            <div class="form-tip">控制生成内容的随机性，值越高越随机，值越低越确定</div>
          </el-form-item>
          
          <el-form-item label="最大令牌数" prop="maxTokens">
            <el-input-number
              v-model="llmSettings.maxTokens"
              :min="100"
              :max="4096"
              :step="100"
              style="width: 200px"
            />
            <div class="form-tip">控制生成内容的最大长度</div>
          </el-form-item>
          
          <el-form-item label="启用缓存" prop="enableCache">
            <el-switch v-model="llmSettings.enableCache" />
          </el-form-item>
          
          <el-form-item label="缓存过期时间(秒)" prop="cacheTtl" :disabled="!llmSettings.enableCache">
            <el-input-number
              v-model="llmSettings.cacheTtl"
              :min="60"
              :max="86400"
              :step="60"
              style="width: 200px"
            />
          </el-form-item>
        </el-form>
      </div>
      
      <!-- 向量数据库设置 -->
      <div v-else-if="activeStep === 1">
        <el-form
          ref="milvusFormRef"
          :model="milvusSettings"
          :rules="milvusRules"
          label-width="150px"
          style="margin-top: 20px"
        >
          <el-form-item label="向量维度" prop="vectorDimension">
            <el-input-number
              v-model="milvusSettings.vectorDimension"
              :min="100"
              :max="4096"
              :step="1"
              style="width: 200px"
            />
            <div class="form-tip">向量嵌入的维度，需与使用的嵌入模型匹配</div>
          </el-form-item>
          
          <el-form-item label="索引类型" prop="indexType">
            <el-select v-model="milvusSettings.indexType" placeholder="请选择索引类型">
              <el-option label="IVF_FLAT" value="IVF_FLAT" />
              <el-option label="IVF_SQ8" value="IVF_SQ8" />
              <el-option label="IVF_PQ" value="IVF_PQ" />
              <el-option label="HNSW" value="HNSW" />
            </el-select>
          </el-form-item>
          
          <el-form-item label="索引参数nlist" prop="nlist" :disabled="milvusSettings.indexType !== 'IVF_FLAT' && milvusSettings.indexType !== 'IVF_SQ8' && milvusSettings.indexType !== 'IVF_PQ'">
            <el-input-number
              v-model="milvusSettings.nlist"
              :min="10"
              :max="10000"
              :step="10"
              style="width: 200px"
            />
            <div class="form-tip">IVF索引的聚类数量</div>
          </el-form-item>
          
          <el-form-item label="搜索参数topK" prop="topK">
            <el-input-number
              v-model="milvusSettings.topK"
              :min="1"
              :max="100"
              :step="1"
              style="width: 200px"
            />
            <div class="form-tip">搜索时返回的最相似向量数量</div>
          </el-form-item>
          
          <el-form-item label="搜索参数nprobe" prop="nprobe">
            <el-input-number
              v-model="milvusSettings.nprobe"
              :min="1"
              :max="100"
              :step="1"
              style="width: 200px"
            />
            <div class="form-tip">搜索时探测的聚类数量</div>
          </el-form-item>
        </el-form>
      </div>
      
      <!-- 缓存设置 -->
      <div v-else-if="activeStep === 2">
        <el-form
          ref="redisFormRef"
          :model="redisSettings"
          :rules="redisRules"
          label-width="150px"
          style="margin-top: 20px"
        >
          <el-form-item label="主机地址" prop="host">
            <el-input v-model="redisSettings.host" placeholder="请输入Redis主机地址" />
          </el-form-item>
          
          <el-form-item label="端口" prop="port">
            <el-input-number
              v-model="redisSettings.port"
              :min="1"
              :max="65535"
              :step="1"
              style="width: 200px"
            />
          </el-form-item>
          
          <el-form-item label="密码" prop="password">
            <el-input v-model="redisSettings.password" type="password" placeholder="请输入Redis密码（如无密码则留空）" show-password />
          </el-form-item>
          
          <el-form-item label="数据库" prop="db">
            <el-input-number
              v-model="redisSettings.db"
              :min="0"
              :max="15"
              :step="1"
              style="width: 200px"
            />
          </el-form-item>
          
          <el-form-item label="连接超时(毫秒)" prop="timeout">
            <el-input-number
              v-model="redisSettings.timeout"
              :min="100"
              :max="30000"
              :step="100"
              style="width: 200px"
            />
          </el-form-item>
        </el-form>
      </div>
      
      <!-- 系统优化 -->
      <div v-else-if="activeStep === 3">
        <el-form
          ref="systemFormRef"
          :model="systemSettings"
          :rules="systemRules"
          label-width="150px"
          style="margin-top: 20px"
        >
          <el-form-item label="文本分块大小" prop="chunkSize">
            <el-input-number
              v-model="systemSettings.chunkSize"
              :min="100"
              :max="5000"
              :step="100"
              style="width: 200px"
            />
            <div class="form-tip">文档处理时的文本分块大小（字符数）</div>
          </el-form-item>
          
          <el-form-item label="分块重叠大小" prop="chunkOverlap">
            <el-input-number
              v-model="systemSettings.chunkOverlap"
              :min="0"
              :max="1000"
              :step="50"
              style="width: 200px"
            />
            <div class="form-tip">相邻分块之间的重叠字符数</div>
          </el-form-item>
          
          <el-form-item label="并行处理数" prop="concurrency">
            <el-input-number
              v-model="systemSettings.concurrency"
              :min="1"
              :max="32"
              :step="1"
              style="width: 200px"
            />
            <div class="form-tip">文档处理的并行线程数</div>
          </el-form-item>
          
          <el-form-item label="最大文档大小(MB)" prop="maxDocumentSize">
            <el-input-number
              v-model="systemSettings.maxDocumentSize"
              :min="1"
              :max="100"
              :step="1"
              style="width: 200px"
            />
            <div class="form-tip">允许上传的单个文档最大大小</div>
          </el-form-item>
          
          <el-form-item label="开启调试模式" prop="debugMode">
            <el-switch v-model="systemSettings.debugMode" />
          </el-form-item>
        </el-form>
      </div>
      
      <!-- 操作按钮 -->
      <div class="form-actions">
        <el-button @click="handlePrevious" v-if="activeStep > 0">上一步</el-button>
        <el-button type="primary" @click="handleNext" v-if="activeStep < 3">下一步</el-button>
        <el-button type="primary" @click="handleSaveAll" v-if="activeStep === 3">保存全部设置</el-button>
        <el-button @click="handleCancel">取消</el-button>
      </div>
    </el-card>
    
    <!-- 高级设置提示 -->
    <el-alert
      title="高级设置提示"
      type="warning"
      :closable="false"
      style="margin-top: 20px"
    >
      <p>1. 部分设置需要重启服务才能生效</p>
      <p>2. 修改向量数据库参数前，请确保了解其影响</p>
      <p>3. 调试模式会记录详细日志，可能影响性能</p>
    </el-alert>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { adminAPI } from '../utils/api'

// 当前步骤
const activeStep = ref(0)

// LLM设置
const llmFormRef = ref()
const llmSettings = reactive({
  defaultModel: 'gpt-3.5-turbo',
  temperature: 0.7,
  maxTokens: 1000,
  enableCache: true,
  cacheTtl: 3600
})

const llmRules = reactive({
  defaultModel: [
    { required: true, message: '请选择默认模型', trigger: 'change' }
  ],
  temperature: [
    { required: true, message: '请设置温度参数', trigger: 'blur' },
    { type: 'number', min: 0, max: 1, message: '温度参数应在0-1之间', trigger: 'blur' }
  ],
  maxTokens: [
    { required: true, message: '请设置最大令牌数', trigger: 'blur' },
    { type: 'number', min: 100, max: 4096, message: '最大令牌数应在100-4096之间', trigger: 'blur' }
  ],
  cacheTtl: [
    { required: true, message: '请设置缓存过期时间', trigger: 'blur' },
    { type: 'number', min: 60, max: 86400, message: '缓存过期时间应在60-86400秒之间', trigger: 'blur' }
  ]
})

// Milvus设置
const milvusFormRef = ref()
const milvusSettings = reactive({
  vectorDimension: 1536,
  indexType: 'IVF_FLAT',
  nlist: 100,
  topK: 5,
  nprobe: 10
})

const milvusRules = reactive({
  vectorDimension: [
    { required: true, message: '请设置向量维度', trigger: 'blur' },
    { type: 'number', min: 100, max: 4096, message: '向量维度应在100-4096之间', trigger: 'blur' }
  ],
  indexType: [
    { required: true, message: '请选择索引类型', trigger: 'change' }
  ],
  nlist: [
    { required: true, message: '请设置索引参数nlist', trigger: 'blur' },
    { type: 'number', min: 10, max: 10000, message: 'nlist应在10-10000之间', trigger: 'blur' }
  ],
  topK: [
    { required: true, message: '请设置搜索参数topK', trigger: 'blur' },
    { type: 'number', min: 1, max: 100, message: 'topK应在1-100之间', trigger: 'blur' }
  ],
  nprobe: [
    { required: true, message: '请设置搜索参数nprobe', trigger: 'blur' },
    { type: 'number', min: 1, max: 100, message: 'nprobe应在1-100之间', trigger: 'blur' }
  ]
})

// Redis设置
const redisFormRef = ref()
const redisSettings = reactive({
  host: 'localhost',
  port: 6379,
  password: '',
  db: 0,
  timeout: 5000
})

const redisRules = reactive({
  host: [
    { required: true, message: '请输入Redis主机地址', trigger: 'blur' }
  ],
  port: [
    { required: true, message: '请设置端口', trigger: 'blur' },
    { type: 'number', min: 1, max: 65535, message: '端口应在1-65535之间', trigger: 'blur' }
  ],
  db: [
    { required: true, message: '请设置数据库', trigger: 'blur' },
    { type: 'number', min: 0, max: 15, message: '数据库编号应在0-15之间', trigger: 'blur' }
  ],
  timeout: [
    { required: true, message: '请设置连接超时', trigger: 'blur' },
    { type: 'number', min: 100, max: 30000, message: '连接超时应在100-30000毫秒之间', trigger: 'blur' }
  ]
})

// 系统设置
const systemFormRef = ref()
const systemSettings = reactive({
  chunkSize: 1000,
  chunkOverlap: 200,
  concurrency: 4,
  maxDocumentSize: 20,
  debugMode: false
})

const systemRules = reactive({
  chunkSize: [
    { required: true, message: '请设置文本分块大小', trigger: 'blur' },
    { type: 'number', min: 100, max: 5000, message: '分块大小应在100-5000字符之间', trigger: 'blur' }
  ],
  chunkOverlap: [
    { required: true, message: '请设置分块重叠大小', trigger: 'blur' },
    { type: 'number', min: 0, max: 1000, message: '重叠大小应在0-1000字符之间', trigger: 'blur' }
  ],
  concurrency: [
    { required: true, message: '请设置并行处理数', trigger: 'blur' },
    { type: 'number', min: 1, max: 32, message: '并行处理数应在1-32之间', trigger: 'blur' }
  ],
  maxDocumentSize: [
    { required: true, message: '请设置最大文档大小', trigger: 'blur' },
    { type: 'number', min: 1, max: 100, message: '最大文档大小应在1-100MB之间', trigger: 'blur' }
  ]
})

// 初始化
onMounted(() => {
  // 加载系统设置
  loadSystemSettings()
})

// 加载系统设置
const loadSystemSettings = async () => {
  try {
    // 从服务器获取设置
    const settings = await adminAPI.getSystemSettings()
    
    // 合并设置到各个表单
    Object.assign(llmSettings, settings.llm)
    Object.assign(milvusSettings, settings.milvus)
    Object.assign(redisSettings, settings.redis)
    Object.assign(systemSettings, settings.system)
    
    console.log('系统设置加载成功')
  } catch (error) {
    console.error('加载系统设置失败:', error)
    // 错误处理已在api.ts中完成
    console.log('使用默认设置值')
  }
}

// 上一步
const handlePrevious = () => {
  activeStep.value--
}

// 下一步
const handleNext = async () => {
  // 验证当前步骤的表单
  if (activeStep.value === 0 && llmFormRef.value) {
    try {
      await llmFormRef.value.validate()
      activeStep.value++
    } catch (error) {
      return
    }
  } else if (activeStep.value === 1 && milvusFormRef.value) {
    try {
      await milvusFormRef.value.validate()
      activeStep.value++
    } catch (error) {
      return
    }
  } else if (activeStep.value === 2 && redisFormRef.value) {
    try {
      await redisFormRef.value.validate()
      activeStep.value++
    } catch (error) {
      return
    }
  }
}

// 保存全部设置
const handleSaveAll = async () => {
  try {
    // 验证最后一步表单
    if (systemFormRef.value) {
      try {
        await systemFormRef.value.validate()
      } catch (error) {
        return
      }
    }
    
    // 构建完整的设置对象
    const allSettings = {
      llm: { ...llmSettings },
      milvus: { ...milvusSettings },
      redis: { ...redisSettings },
      system: { ...systemSettings }
    }
    
    // 发送保存请求
    await adminAPI.saveSystemSettings(allSettings)
    
    ElMessage.success('系统设置保存成功')
    
    // 显示重启提示
    ElMessageBox.alert(
      '设置已保存，部分设置需要重启服务才能生效。',
      '提示',
      {
        confirmButtonText: '确定',
        type: 'info'
      }
    )
  } catch (error) {
    console.error('保存系统设置失败:', error)
    // 错误处理已在api.ts中完成
  }
}

// 取消
const handleCancel = () => {
  ElMessageBox.confirm(
    '确定要取消设置吗？未保存的更改将会丢失。',
    '确认取消',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  )
    .then(() => {
      // 重置表单
      loadSystemSettings()
      activeStep.value = 0
    })
    .catch(() => {
      // 什么都不做
    })
}
</script>

<style scoped>
.system-settings {
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

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}

.form-actions {
  margin-top: 30px;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
</style>