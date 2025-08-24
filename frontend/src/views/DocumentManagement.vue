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
      <el-upload
        class="upload-demo"
        ref="uploadRef"
        :http-request="handleHttpRequest"
        :on-success="handleUploadSuccess"
        :on-error="handleUploadError"
        :file-list="fileList"
        :auto-upload="false"
        accept=".pdf,.docx,.doc,.txt"
        drag
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
          <el-button @click="handleCloseUploadDialog">取消</el-button>
          <el-button type="primary" @click="submitUpload">上传</el-button>
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
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="text" @click="deleteDocument(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <div class="pagination" v-if="documents.length > 0">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
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
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ragAPI } from '../utils/api'

// 上传相关
const showUploadDialog = ref(false)
const uploadRef = ref()
const fileList = ref([])
const uploadProgress = ref(0)

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

// 初始化时加载文档列表
onMounted(() => {
  fetchDocuments()
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

// 提交上传
const submitUpload = () => {
  if (!uploadRef.value) return
  uploadRef.value.submit()
}

// 自定义HTTP请求处理
const handleHttpRequest = async (options) => {
  const file = options.file
  const formData = new FormData()
  formData.append('file', file)
  
  try {
    // 使用ragAPI上传文档
    const response = await ragAPI.uploadDocument(formData)
    options.onSuccess(response)
  } catch (error) {
    options.onError(error)
  }
}

// 处理上传成功
const handleUploadSuccess = (response) => {
  ElMessage.success('文档上传成功')
  fetchDocuments() // 重新获取文档列表
  showUploadDialog.value = false
  fileList.value = []
}

// 处理上传失败
const handleUploadError = (error) => {
  console.error('文档上传失败:', error)
  // 错误处理已在api.ts中完成
}



// 关闭上传对话框
const handleCloseUploadDialog = () => {
  fileList.value = []
  showUploadDialog.value = false
}

// 删除文档
const deleteDocument = (documentId) => {
  ElMessageBox.confirm(
    '确定要删除这个文档吗？此操作无法撤销。',
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