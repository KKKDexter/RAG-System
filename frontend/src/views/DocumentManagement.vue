<template>
  <div class="document-management">
    <div class="page-header">
      <h1>知识库管理</h1>
      <el-button type="primary" @click="showUploadDialog = true">
        <el-icon><Upload /></el-icon>上传文档
      </el-button>
    </div>
    
    <!-- 上传文档对话框 -->
    <el-dialog
      v-model="showUploadDialog"
      title="上传文档"
      width="500px"
      :before-close="handleCloseUploadDialog"
    >
      <!-- Embedding模型选择 -->
      <div class="model-selection" style="margin-bottom: 20px;">
        <el-form-item label="Embedding模型" label-width="120px">
          <el-select 
            v-model="selectedEmbeddingModelId" 
            placeholder="请选择embedding模型（可选）"
            clearable
            style="width: 100%"
          >
            <el-option 
              v-for="model in embeddingModels" 
              :key="model.id" 
              :label="`${model.name} ${model.is_local ? '(本地)' : '(API)'}`" 
              :value="model.id"
            >
              <span style="float: left">{{ model.name }}</span>
              <span style="float: right; color: #8492a6; font-size: 13px">
                {{ model.is_local ? '本地模型' : 'API模型' }}
              </span>
            </el-option>
          </el-select>
          <div class="form-tip" style="margin-top: 5px; color: #909399; font-size: 12px;">
            选择用于生成文档向量的embedding模型，不选择将使用默认模型
          </div>
        </el-form-item>
      </div>
      
      <el-upload
        class="upload-demo"
        ref="uploadRef"
        :file-list="fileList"
        :auto-upload="false"
        :multiple="true"
        accept=".pdf,.docx,.doc,.txt"
        drag
        :disabled="isUploading"
      >
        <el-icon class="el-icon--upload"><Upload /></el-icon>
        <div class="el-upload__text">
          点击或拖拽文件到此区域选择
        </div>
        <div class="el-upload__tip" slot="tip">
          支持 .pdf, .docx, .doc, .txt 格式的文件，单个文件大小不超过10MB，可选择多个文件
        </div>
      </el-upload>
      
      <!-- 上传进度显示 -->
      <div v-if="isUploading" class="upload-progress" style="margin-top: 20px;">
        <div class="progress-header">
          <span>上传进度: {{ uploadedCount }} / {{ totalCount }}</span>
          <span class="progress-percentage">{{ Math.round((uploadedCount / totalCount) * 100) }}%</span>
        </div>
        <el-progress 
          :percentage="Math.round((uploadedCount / totalCount) * 100)"
          :stroke-width="20"
          status="success"
        />
        <div class="upload-file-list" style="margin-top: 10px; max-height: 200px; overflow-y: auto;">
          <div 
            v-for="(file, index) in fileList" 
            :key="index" 
            class="upload-file-item"
            :class="{
              'uploading': file.status === 'uploading',
              'success': file.status === 'success',
              'error': file.status === 'error'
            }"
          >
            <el-icon v-if="file.status === 'uploading'" class="is-loading"><Loading /></el-icon>
            <el-icon v-else-if="file.status === 'success'" class="success-icon"><Check /></el-icon>
            <el-icon v-else-if="file.status === 'error'" class="error-icon"><Close /></el-icon>
            <el-icon v-else><Document /></el-icon>
            <span class="file-name">{{ file.name }}</span>
            <span v-if="file.status === 'error'" class="error-message">{{ file.errorMessage }}</span>
          </div>
        </div>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="handleCloseUploadDialog">取消</el-button>
          <el-button 
            type="primary" 
            @click="submitUpload" 
            :loading="isUploading"
            :disabled="fileList.length === 0"
          >
            {{ isUploading ? '上传中...' : `上传 (${fileList.length}个文件)` }}
          </el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- 文档列表 -->
    <el-card class="document-list-card">
      <template #header>
        <div class="card-header">
          <span>我的文档</span>
          <div class="header-actions">
            <el-input
              v-model="searchQuery"
              placeholder="搜索文档名称"
              prefix-icon="Search"
              style="width: 200px;"
              @input="handleSearch"
            />
          </div>
        </div>
      </template>
      
      <el-table
        v-loading="isLoading"
        :data="filteredDocuments"
        style="width: 100%"
        stripe
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="original_filename" label="文件名" min-width="200">
          <template #default="{ row }">
            <el-link type="primary" @click="viewDocument(row)">{{ row.original_filename }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="uploaded_at" label="上传时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.uploaded_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="260" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="editDocument(row)">编辑</el-button>
            <el-button type="warning" size="small" @click="updateDocumentFile(row)">更新文件</el-button>
            <el-button type="danger" size="small" @click="deleteDocument(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <div class="pagination" v-if="documents.length > 0">
        <el-pagination
          :current-page="currentPage"
          :page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="documents.length"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
      
      <!-- 空状态 -->
      <div v-else-if="!isLoading" class="empty-state">
        <el-empty description="暂无文档" />
        <el-button type="primary" @click="showUploadDialog = true" style="margin-top: 20px;">
          立即上传
        </el-button>
      </div>
    </el-card>
    
    <!-- 编辑文档对话框 -->
    <el-dialog
      v-model="showEditDialog"
      title="编辑文档"
      width="500px"
    >
      <el-form
        ref="editFormRef"
        :model="editForm"
        :rules="editRules"
        label-width="100px"
      >
        <el-form-item label="文件名" prop="original_filename">
          <el-input v-model="editForm.original_filename" placeholder="请输入文件名" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showEditDialog = false">取消</el-button>
          <el-button type="primary" @click="handleEditSubmit">确定</el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- 更新文件对话框 -->
    <el-dialog
      v-model="showUpdateFileDialog"
      title="更新文档文件"
      width="500px"
      :before-close="handleCloseUpdateFileDialog"
    >
      <div class="update-file-info">
        <p><strong>当前文档：</strong>{{ currentDocument?.original_filename }}</p>
        <p class="warning-text">注意：更新文件将替换原有文档内容，并重新生成向量索引。</p>
      </div>
      
      <!-- Embedding模型选择 -->
      <div class="model-selection" style="margin-bottom: 20px;">
        <el-form-item label="Embedding模型" label-width="120px">
          <el-select 
            v-model="selectedUpdateEmbeddingModelId" 
            placeholder="请选择embedding模型（可选）"
            clearable
            style="width: 100%"
          >
            <el-option 
              v-for="model in embeddingModels" 
              :key="model.id" 
              :label="`${model.name} ${model.is_local ? '(本地)' : '(API)'}`" 
              :value="model.id"
            >
              <span style="float: left">{{ model.name }}</span>
              <span style="float: right; color: #8492a6; font-size: 13px">
                {{ model.is_local ? '本地模型' : 'API模型' }}
              </span>
            </el-option>
          </el-select>
          <div class="form-tip" style="margin-top: 5px; color: #909399; font-size: 12px;">
            选择用于重新生成文档向量的embedding模型，不选择将使用默认模型
          </div>
        </el-form-item>
      </div>
      
      <el-upload
        class="upload-demo"
        ref="updateFileUploadRef"
        :http-request="handleUpdateFileHttpRequest"
        :on-success="handleUpdateFileSuccess"
        :on-error="handleUpdateFileError"
        :file-list="updateFileList"
        :auto-upload="false"
        accept=".pdf,.docx,.doc,.txt"
        drag
        :limit="1"
      >
        <el-icon class="el-icon--upload"><Upload /></el-icon>
        <div class="el-upload__text">
          点击或拖拽文件到此区域上传
        </div>
        <div class="el-upload__tip" slot="tip">
          支持 .pdf, .docx, .doc, .txt 格式的文件，单个文件大小不超过10MB
        </div>
      </el-upload>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="handleCloseUpdateFileDialog">取消</el-button>
          <el-button type="primary" @click="submitUpdateFile" :disabled="updateFileList.length === 0">更新</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload, Loading, Check, Close, Document } from '@element-plus/icons-vue'
import { ragAPI } from '../utils/api.js'

// 上传相关
const showUploadDialog = ref(false)
const uploadRef = ref()
const fileList = ref([])
const uploadProgress = ref(0)
const isUploading = ref(false)
const uploadedCount = ref(0)
const totalCount = ref(0)

// Embedding模型选择
const embeddingModels = ref([])
const selectedEmbeddingModelId = ref(null)

// 编辑相关
const showEditDialog = ref(false)
const editFormRef = ref()
const editForm = reactive({
  id: null,
  original_filename: ''
})

// 更新文件相关
const showUpdateFileDialog = ref(false)
const updateFileUploadRef = ref()
const updateFileList = ref([])
const currentDocument = ref(null)
const selectedUpdateEmbeddingModelId = ref(null)

// 编辑表单验证规则
const editRules = reactive({
  original_filename: [
    { required: true, message: '请输入文件名', trigger: 'blur' },
    { min: 1, max: 255, message: '文件名长度在 1 到 255 个字符', trigger: 'blur' }
  ]
})

// 文档列表相关
const documents = ref([])
const isLoading = ref(false)
const searchQuery = ref('')
const currentPage = ref(1)
const pageSize = ref(10)

// 过滤后的文档列表
const filteredDocuments = computed(() => {
  if (!searchQuery.value) {
    return documents.value
  }
  return documents.value.filter(doc => 
    doc.original_filename.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
})

// 初始化时加载文档列表和embedding模型列表
onMounted(() => {
  fetchDocuments()
  fetchEmbeddingModels()
})

// 获取文档列表
const fetchDocuments = async () => {
  try {
    isLoading.value = true
    documents.value = await ragAPI.getDocuments()
  } catch (error) {
    console.error('获取文档列表失败:', error)
    // 错误处理已在api.ts中完成
  } finally {
    isLoading.value = false
  }
}

// 获取可用的embedding模型列表
const fetchEmbeddingModels = async () => {
  try {
    embeddingModels.value = await ragAPI.getEmbeddingModels()
    console.log('成功加载', embeddingModels.value.length, '个embedding模型')
  } catch (error) {
    console.error('获取embedding模型列表失败:', error)
    // 错误处理已在api.js中完成
  }
}

// 提交上传
const submitUpload = async () => {
  if (fileList.value.length === 0) {
    ElMessage.warning('请先选择要上传的文件')
    return
  }
  
  isUploading.value = true
  uploadedCount.value = 0
  totalCount.value = fileList.value.length
  
  // 初始化所有文件状态
  fileList.value.forEach(file => {
    file.status = 'waiting'
  })
  
  try {
    // 使用Promise.all并发上传，但限制并发数量以避免过载
    const batchSize = 3 // 同时最多上传3个文件
    const batches = []
    
    for (let i = 0; i < fileList.value.length; i += batchSize) {
      const batch = fileList.value.slice(i, i + batchSize)
      batches.push(batch)
    }
    
    let successCount = 0
    let errorCount = 0
    const uploadResults = []
    
    for (const batch of batches) {
      const promises = batch.map(async (fileItem) => {
        try {
          // 设置文件状态为上传中
          fileItem.status = 'uploading'
          
          const formData = new FormData()
          formData.append('file', fileItem.raw)
          
          // 如果选择了embedding模型，则添加到请求中
          if (selectedEmbeddingModelId.value) {
            formData.append('embedding_model_id', selectedEmbeddingModelId.value)
          }
          
          await ragAPI.uploadDocument(formData)
          
          // 上传成功
          fileItem.status = 'success'
          uploadedCount.value++
          successCount++
          uploadResults.push({ file: fileItem.name, success: true })
          console.log(`文件 ${fileItem.name} 上传成功`)
        } catch (error) {
          // 上传失败
          fileItem.status = 'error'
          fileItem.errorMessage = error.response?.data?.detail || error.message || '上传失败'
          errorCount++
          uploadResults.push({ file: fileItem.name, success: false, error: fileItem.errorMessage })
          console.error(`文件 ${fileItem.name} 上传失败:`, error)
        }
      })
      
      await Promise.all(promises)
    }
    
    // 等待一秒让用户看到完成状态
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    // 显示详细结果
    if (errorCount === 0) {
      ElMessage.success(`所有文件上传成功！共上传 ${successCount} 个文件`)
    } else if (successCount > 0) {
      const successFiles = uploadResults.filter(r => r.success).map(r => r.file)
      const errorFiles = uploadResults.filter(r => !r.success)
      
      ElMessage({
        type: 'warning',
        duration: 6000,
        dangerouslyUseHTMLString: true,
        message: `
          <div>
            <p>部分文件上传成功：${successCount} 个成功，${errorCount} 个失败</p>
            <details style="margin-top: 10px;">
              <summary style="cursor: pointer; color: #409EFF;">查看详情</summary>
              <div style="margin-top: 5px;">
                <p style="color: #67C23A;">成功: ${successFiles.join(', ')}</p>
                <p style="color: #F56C6C;">失败: ${errorFiles.map(f => `${f.file}(${f.error})`).join(', ')}</p>
              </div>
            </details>
          </div>
        `
      })
    } else {
      const errorMessages = uploadResults.filter(r => !r.success).map(r => `${r.file}: ${r.error}`).join('\n')
      ElMessage({
        type: 'error',
        duration: 8000,
        message: `所有文件上传失败：\n${errorMessages}`
      })
    }
    
    // 刷新文档列表
    if (successCount > 0) {
      fetchDocuments()
    }
    
    // 延迟关闭对话框，让用户看到结果
    setTimeout(() => {
      showUploadDialog.value = false
      fileList.value = []
      selectedEmbeddingModelId.value = null
    }, 2000)
    
  } catch (error) {
    console.error('批量上传失败:', error)
    ElMessage.error('上传过程中发生错误')
  } finally {
    isUploading.value = false
    uploadedCount.value = 0
    totalCount.value = 0
  }
}

// 关闭上传对话框
const handleCloseUploadDialog = () => {
  if (isUploading.value) {
    ElMessageBox.confirm(
      '上传正在进行中，确定要取消吗？',
      '确认取消',
      {
        confirmButtonText: '确定',
        cancelButtonText: '继续上传',
        type: 'warning'
      }
    ).then(() => {
      fileList.value = []
      selectedEmbeddingModelId.value = null
      showUploadDialog.value = false
      isUploading.value = false
    }).catch(() => {
      // 用户选择继续上传
    })
  } else {
    fileList.value = []
    selectedEmbeddingModelId.value = null
    showUploadDialog.value = false
  }
}

// 编辑文档
const editDocument = (document) => {
  editForm.id = document.id
  editForm.original_filename = document.original_filename
  showEditDialog.value = true
}

// 更新文档文件
const updateDocumentFile = (document) => {
  currentDocument.value = document
  updateFileList.value = []
  selectedUpdateEmbeddingModelId.value = null
  showUpdateFileDialog.value = true
}

// 提交更新文件
const submitUpdateFile = () => {
  if (!updateFileUploadRef.value) return
  updateFileUploadRef.value.submit()
}

// 自定义更新文件HTTP请求处理
const handleUpdateFileHttpRequest = async (options) => {
  const file = options.file
  const formData = new FormData()
  formData.append('file', file)
  
  // 如果选择了embedding模型，则添加到请求中
  if (selectedUpdateEmbeddingModelId.value) {
    formData.append('embedding_model_id', selectedUpdateEmbeddingModelId.value)
  }
  
  try {
    // 使用ragAPI更新文档文件
    const response = await ragAPI.updateDocumentFile(currentDocument.value.id, formData)
    options.onSuccess(response)
  } catch (error) {
    options.onError(error)
  }
}

// 处理更新文件成功
const handleUpdateFileSuccess = (response) => {
  ElMessage.success('文档文件更新成功')
  fetchDocuments() // 重新获取文档列表
  showUpdateFileDialog.value = false
  updateFileList.value = []
  currentDocument.value = null
}

// 处理更新文件失败
const handleUpdateFileError = (error) => {
  console.error('文档文件更新失败:', error)
  // 错误处理已在api.js中完成
}

// 关闭更新文件对话框
const handleCloseUpdateFileDialog = () => {
  updateFileList.value = []
  currentDocument.value = null
  selectedUpdateEmbeddingModelId.value = null
  showUpdateFileDialog.value = false
}

// 提交编辑
const handleEditSubmit = async () => {
  if (!editFormRef.value) return
  
  try {
    // 验证表单
    await editFormRef.value.validate()
    
    // 更新文档
    await ragAPI.updateDocument(editForm.id, {
      original_filename: editForm.original_filename
    })
    
    ElMessage.success('文档更新成功')
    showEditDialog.value = false
    fetchDocuments() // 重新获取文档列表
  } catch (error) {
    console.error('更新文档失败:', error)
    // 错误处理已在api.js中完成
  }
}

// 删除文档
const deleteDocument = (documentId) => {
  ElMessageBox.confirm(
    '确定要删除这个文档吗？文档将被移入回收站。',
    '确认删除',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  )
    .then(async () => {
      try {
        await ragAPI.deleteDocument(documentId)
        ElMessage.success('文档删除成功')
        fetchDocuments() // 重新获取文档列表
      } catch (error) {
        console.error('删除文档失败:', error)
        // 错误处理已在api.ts中完成
      }
    })
    .catch(() => {
      ElMessage.info('已取消删除')
    })
}

// 查看文档
const viewDocument = (document) => {
  ElMessage.info('查看文档功能待实现')
}

// 搜索文档
const handleSearch = () => {
  currentPage.value = 1 // 重置到第一页
}

// 分页处理
const handleSizeChange = (size) => {
  pageSize.value = size
}

const handleCurrentChange = (current) => {
  currentPage.value = current
}

// 格式化日期
const formatDate = (dateString) => {
  const date = new Date(dateString)
  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  }).format(date)
}
</script>

<style scoped>
.document-management {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0;
  color: #333;
}

.document-list-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
}

/* 上传组件样式 */
.upload-demo {
  border: 2px dashed #d9d9d9;
  border-radius: 6px;
  padding: 40px 20px;
  text-align: center;
  cursor: pointer;
}

.upload-demo:hover {
  border-color: #409eff;
}

.dialog-footer {
  text-align: right;
}

/* 更新文件对话框样式 */
.update-file-info {
  margin-bottom: 20px;
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 6px;
}

.update-file-info p {
  margin: 0 0 8px 0;
  color: #333;
}

.warning-text {
  color: #e6a23c !important;
  font-size: 14px;
}

/* 上传进度样式 */
.upload-progress {
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  padding: 15px;
  background-color: #fafafa;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  font-weight: 600;
  color: #303133;
}

.progress-percentage {
  color: #67c23a;
  font-size: 16px;
}

.upload-file-list {
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  background-color: #ffffff;
  padding: 10px;
}

.upload-file-item {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  margin-bottom: 6px;
  border-radius: 4px;
  transition: all 0.3s;
  border: 1px solid transparent;
}

.upload-file-item:last-child {
  margin-bottom: 0;
}

.upload-file-item.uploading {
  background-color: #ecf5ff;
  border-color: #b3d8ff;
}

.upload-file-item.success {
  background-color: #f0f9ff;
  border-color: #b3e5fc;
}

.upload-file-item.error {
  background-color: #fef0f0;
  border-color: #fbc4c4;
}

.upload-file-item .el-icon {
  margin-right: 8px;
  font-size: 16px;
}

.upload-file-item .success-icon {
  color: #67c23a;
}

.upload-file-item .error-icon {
  color: #f56c6c;
}

.upload-file-item .file-name {
  flex: 1;
  font-size: 14px;
  color: #303133;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.upload-file-item .error-message {
  font-size: 12px;
  color: #f56c6c;
  margin-left: 10px;
  max-width: 200px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .header-actions {
    width: 100%;
    flex-direction: column;
  }
  
  .header-actions .el-input {
    width: 100% !important;
  }
  
  .pagination {
    justify-content: center;
  }
}
</style>