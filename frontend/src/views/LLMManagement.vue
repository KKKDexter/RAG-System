<template>
  <div class="llm-management-container">
    <el-card class="page-card">
      <template #header>
          <el-button type="primary" @click="handleAddModel" icon="el-icon-plus" size="small">
            添加大模型
>>>>>>> main
          </el-button>
        </div>
        <div class="card-header">
          <span>大模型管理</span>
          <el-button type="primary" @click="handleAddModel" size="small">
            <el-icon><Plus /></el-icon>添加大模型
          </el-button>
        </div>
=======
          <el-button type="primary" @click="handleAddModel" icon="el-icon-plus" size="small">
            添加大模型
>>>>>>> main
          </el-button>
        </div>
      </template>

      <div class="filter-container">
        <el-select v-model="filterType" placeholder="筛选类型" size="small" @change="handleFilterChange">
          <el-option label="全部" value=""></el-option>
          <el-option label="聊天模型" value="chat"></el-option>
          <el-option label="嵌入模型" value="embedding"></el-option>
          <el-option label="重排模型" value="rerank"></el-option>
        </el-select>
        <el-input
          v-model="filterName"
          placeholder="搜索模型名称"
          size="small"
          :prefix-icon="Search"
          style="margin-left: 10px; width: 200px;"
          @input="handleSearch"
        ></el-input>
      </div>

      <el-table :data="modelsList" style="width: 100%" v-loading="loading">
        <el-table-column prop="id" label="ID" width="80"></el-table-column>
        <el-table-column prop="name" label="模型名称" width="180"></el-table-column>
        <el-table-column prop="type" label="模型类型" width="120">
          <template #default="scope">
            <el-tag
              :type="scope.row.type === 'chat' ? 'primary' : scope.row.type === 'embedding' ? 'success' : 'warning'"
              size="small"
            >
              {{ scope.row.type === 'chat' ? '聊天模型' : scope.row.type === 'embedding' ? '嵌入模型' : '重排模型' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="base_url" label="基础URL" width="300"></el-table-column>
        <el-table-column prop="is_active" label="是否激活" width="100">
          <template #default="scope">
            <el-switch v-model="scope.row.is_active" :active-value="true" :inactive-value="false" @change="handleStatusChange(scope.row)"></el-switch>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180"></el-table-column>
        <el-table-column prop="updated_at" label="更新时间" width="180"></el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
            <el-button type="primary" icon="el-icon-edit" size="small" @click="handleEditModel(scope.row)"></el-button>
            <el-button type="danger" icon="el-icon-delete" size="small" @click="handleDeleteModel(scope.row)"></el-button>
>>>>>>> main
          </template>
          <template #default="scope">
            <el-button type="primary" size="small" @click="handleEditModel(scope.row)">
              <el-icon><Edit /></el-icon>
            </el-button>
            <el-button type="danger" size="small" @click="handleDeleteModel(scope.row)">
              <el-icon><Delete /></el-icon>
            </el-button>
          </template>
=======
            <el-button type="primary" icon="el-icon-edit" size="small" @click="handleEditModel(scope.row)"></el-button>
            <el-button type="danger" icon="el-icon-delete" size="small" @click="handleDeleteModel(scope.row)"></el-button>
>>>>>>> main
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-container">
        <el-pagination
<<<<<<< HEAD
          :current-page="currentPage"
          :page-size="pageSize"
=======
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
>>>>>>> main
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="total"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        ></el-pagination>
      </div>
    </el-card>

    <!-- 添加/编辑模型对话框 -->
    <el-dialog v-model="dialogVisible" title="{{ dialogTitle }}" width="600px">
      <el-form :model="modelForm" :rules="rules" ref="modelFormRef" label-width="100px">
        <el-form-item label="模型名称" prop="name">
          <el-input v-model="modelForm.name" placeholder="请输入模型名称"></el-input>
        </el-form-item>
        <el-form-item label="模型类型" prop="type">
          <el-select v-model="modelForm.type" placeholder="请选择模型类型">
            <el-option label="聊天模型" value="chat"></el-option>
            <el-option label="嵌入模型" value="embedding"></el-option>
            <el-option label="重排模型" value="rerank"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="API密钥" prop="api_key">
          <el-input v-model="modelForm.api_key" placeholder="请输入API密钥" show-password></el-input>
        </el-form-item>
        <el-form-item label="基础URL" prop="base_url">
          <el-input v-model="modelForm.base_url" placeholder="请输入基础URL"></el-input>
        </el-form-item>
        <el-form-item label="模型参数">
          <el-input
            v-model="modelForm.model_params"
            type="textarea"
            placeholder="请输入模型参数(JSON格式)"
            :rows="4"
          ></el-input>
        </el-form-item>
        <el-form-item label="是否激活">
          <el-switch v-model="modelForm.is_active" :active-value="true" :inactive-value="false"></el-switch>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
<<<<<<< HEAD
import { Search, Plus, Edit, Delete } from '@element-plus/icons-vue'
=======
import { Search } from '@element-plus/icons-vue'
>>>>>>> main
import { llmAPI } from '../utils/api'

// 表格数据和分页
defineProps({
  // 可以添加props
})

const modelsList = ref([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)

// 筛选条件
const filterType = ref('')
const filterName = ref('')

// 对话框数据
const dialogVisible = ref(false)
const dialogTitle = ref('添加大模型')
const modelForm = reactive({
  id: '',
  name: '',
  type: '',
  api_key: '',
  base_url: '',
  model_params: '',
  is_active: true
})
const modelFormRef = ref(null)

// 表单验证规则
const rules = {
  name: [
    { required: true, message: '请输入模型名称', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符之间', trigger: 'blur' }
  ],
  type: [
    { required: true, message: '请选择模型类型', trigger: 'change' }
  ],
  api_key: [
    { required: true, message: '请输入API密钥', trigger: 'blur' }
  ],
  base_url: [
    { required: true, message: '请输入基础URL', trigger: 'blur' },
    { type: 'url', message: '请输入有效的URL', trigger: 'blur' }
  ]
}

// 生命周期钩子
onMounted(() => {
  fetchModels()
})

// 获取模型列表
const fetchModels = async () => {
  loading.value = true
  try {
    const params = {
      skip: (currentPage.value - 1) * pageSize.value,
      limit: pageSize.value,
      is_delete: false
    }
    
    if (filterType.value) {
      params.type = filterType.value
    }
    
    if (filterName.value) {
      params.name = filterName.value
    }
    
    const response = await llmAPI.getModels(params)
    modelsList.value = response
    total.value = response.length // 实际项目中应该从后端获取total
    loading.value = false
  } catch (error) {
    console.error('获取模型列表失败:', error)
    ElMessage.error('获取模型列表失败')
    loading.value = false
  }
}

// 处理添加模型
const handleAddModel = () => {
  dialogTitle.value = '添加大模型'
  modelForm.id = ''
  modelForm.name = ''
  modelForm.type = ''
  modelForm.api_key = ''
  modelForm.base_url = ''
  modelForm.model_params = ''
  modelForm.is_active = true
  dialogVisible.value = true
  if (modelFormRef.value) {
    modelFormRef.value.resetFields()
  }
}

// 处理编辑模型
const handleEditModel = (row) => {
  dialogTitle.value = '编辑大模型'
  modelForm.id = row.id
  modelForm.name = row.name
  modelForm.type = row.type
  modelForm.api_key = row.api_key
  modelForm.base_url = row.base_url
  modelForm.model_params = row.model_params || ''
  modelForm.is_active = row.is_active
  dialogVisible.value = true
}

// 处理提交表单
const handleSubmit = async () => {
  try {
    await modelFormRef.value.validate()
    
    // 处理模型参数
    let params = modelForm.model_params
    if (params) {
      try {
        params = JSON.parse(params)
      } catch (e) {
        ElMessage.error('模型参数格式不正确，请输入有效的JSON')
        return
      }
    }
    
    const formData = {
      name: modelForm.name,
      type: modelForm.type,
      api_key: modelForm.api_key,
      base_url: modelForm.base_url,
      model_params: params,
      is_active: modelForm.is_active
    }
    
    if (modelForm.id) {
      // 更新模型
      await llmAPI.updateModel(modelForm.id, formData)
      ElMessage.success('模型更新成功')
    } else {
      // 创建模型
      await llmAPI.createModel(formData)
      ElMessage.success('模型创建成功')
    }
    
    dialogVisible.value = false
    fetchModels()
  } catch (error) {
    console.error('提交表单失败:', error)
    ElMessage.error('提交表单失败')
  }
}

// 处理删除模型
const handleDeleteModel = async (row) => {
  try {
    await llmAPI.deleteModel(row.id)
    ElMessage.success('模型删除成功')
    fetchModels()
  } catch (error) {
    console.error('删除模型失败:', error)
    ElMessage.error('删除模型失败')
  }
}

// 处理状态变更
const handleStatusChange = async (row) => {
  try {
    await llmAPI.updateModel(row.id, { is_active: row.is_active })
    ElMessage.success('状态更新成功')
  } catch (error) {
    console.error('更新状态失败:', error)
    ElMessage.error('更新状态失败')
    // 回滚状态
    row.is_active = !row.is_active
  }
}

// 处理筛选变更
const handleFilterChange = () => {
  currentPage.value = 1
  fetchModels()
}

// 处理搜索
const handleSearch = () => {
  currentPage.value = 1
  fetchModels()
}

// 分页处理
const handleSizeChange = (size) => {
  pageSize.value = size
  currentPage.value = 1
  fetchModels()
}

const handleCurrentChange = (current) => {
  currentPage.value = current
  fetchModels()
}
</script>

<style scoped>
.llm-management-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-container {
  display: flex;
  margin-bottom: 16px;
  align-items: center;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>