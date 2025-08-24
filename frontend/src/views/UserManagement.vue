<template>
  <div class="user-management">
    <div class="page-header">
      <h1>用户管理</h1>
      <p>管理所有用户账号、角色和权限</p>
    </div>
    
    <!-- 操作按钮 -->
    <div class="action-buttons">
      <el-button type="primary" @click="handleAddUser">
        <el-icon><Plus /></el-icon>新增用户
      </el-button>
      <el-button @click="handleRefresh">
        <el-icon><Refresh /></el-icon>刷新
      </el-button>
    </div>
    
    <!-- 搜索和筛选 -->
    <div class="search-filter">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索用户名或邮箱"
        prefix-icon="Search"
        style="width: 300px"
        @keyup.enter="handleSearch"
      />
      <el-select
        v-model="roleFilter"
        placeholder="筛选角色"
        style="margin-left: 15px; width: 150px"
        @change="handleSearch"
      >
        <el-option label="全部" value="" />
        <el-option label="管理员" value="admin" />
        <el-option label="普通用户" value="user" />
      </el-select>
      <el-button type="primary" @click="handleSearch" style="margin-left: 15px">
        <el-icon><Search /></el-icon>搜索
      </el-button>
    </div>
    
    <!-- 表格和分页容器 -->
    <div class="table-and-pagination-container">
      <!-- 表格容器 -->
      <div class="table-container">
        <!-- 用户列表 -->
        <el-table
          v-loading="loading"
          :data="usersData"
          border
          style="width: 100%; max-width: 100%;"
          :table-layout="'fixed'"
          :show-overflow-tooltip="true"
          :size="'default'"
          :max-height="tableHeight"
        >
          <el-table-column type="index" width="60" />
          
          <el-table-column prop="username" label="用户名" sortable show-overflow-tooltip>
            <template #default="scope">
              <div class="user-info">
                <el-avatar size="small" style="margin-right: 10px">{{ scope.row.username?.charAt(0).toUpperCase() }}</el-avatar>
                <span>{{ scope.row.username }}</span>
              </div>
            </template>
          </el-table-column>
          
          <el-table-column prop="email" label="邮箱" sortable show-overflow-tooltip />
          
          <el-table-column prop="phone" label="手机号" show-overflow-tooltip />
          
          <el-table-column prop="role" label="角色" sortable>
            <template #default="scope">
              <el-tag :type="scope.row.role === 'admin' ? 'primary' : 'success'">
                {{ scope.row.role === 'admin' ? '管理员' : '普通用户' }}
              </el-tag>
            </template>
          </el-table-column>
          
          <el-table-column prop="created_at" label="创建时间" sortable show-overflow-tooltip>
            <template #default="scope">
              {{ formatDate(scope.row.created_at) }}
            </template>
          </el-table-column>
          
          <el-table-column label="操作" width="160" fixed="right">
            <template #default="scope">
              <el-button
                type="primary"
                size="small"
                @click="handleEditUser(scope.row)"
                :disabled="scope.row.id === currentUserId"
              >
                编辑
              </el-button>
              <el-button
                type="danger"
                size="small"
                @click="handleDeleteUser(scope.row)"
                :disabled="scope.row.id === currentUserId"
              >
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      
      <!-- 分页 -->
      <div class="pagination" style="margin-top: 0px !important; margin-bottom: 0 !important; padding-top: 12px; border-top: 1px solid #ebeef5; position: relative; z-index: 10;">
        <el-pagination
          :current-page="currentPage"
          :page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="total"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </div>
    
    <!-- 新增/编辑用户对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditMode ? '编辑用户' : '新增用户'"
      width="500px"
    >
      <el-form
        ref="userFormRef"
        :model="userForm"
        :rules="userRules"
        label-width="100px"
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="userForm.username" placeholder="请输入用户名" />
        </el-form-item>
        
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="userForm.email" placeholder="请输入邮箱" />
        </el-form-item>
        
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="userForm.phone" placeholder="请输入手机号" />
        </el-form-item>
        
        <el-form-item label="角色" prop="role">
          <el-select v-model="userForm.role" placeholder="请选择角色">
            <el-option label="管理员" value="admin" />
            <el-option label="普通用户" value="user" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="密码" prop="password" v-if="!isEditMode">
          <el-input v-model="userForm.password" type="password" placeholder="请输入密码" />
        </el-form-item>
        
        <el-form-item label="确认密码" prop="confirmPassword" v-if="!isEditMode">
          <el-input v-model="userForm.confirmPassword" type="password" placeholder="请再次输入密码" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSubmit">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, computed, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh, Search } from '@element-plus/icons-vue'
import { adminAPI } from '../utils/api.js'

// 用户数据
const users = ref([])
const loading = ref(false)
const searchKeyword = ref('')
const roleFilter = ref('')
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const currentUserId = ref(null)

// 表格高度自适应
const tableHeight = ref(400)

// 计算当前页的用户数据
const usersData = computed(() => {
  let filtered = [...users.value]
  
  // 搜索筛选
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    filtered = filtered.filter(user => 
      user.username?.toLowerCase().includes(keyword) ||
      user.email?.toLowerCase().includes(keyword)
    )
  }
  
  // 角色筛选
  if (roleFilter.value) {
    filtered = filtered.filter(user => user.role === roleFilter.value)
  }
  
  // 分页
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  total.value = filtered.length
  
  return filtered.slice(start, end)
})

// 对话框相关
const dialogVisible = ref(false)
const isEditMode = ref(false)
const userFormRef = ref()

// 用户表单
const userForm = reactive({
  id: null,
  username: '',
  email: '',
  phone: '',
  role: 'user',
  password: '',
  confirmPassword: ''
})

// 表单验证规则
const userRules = reactive({
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  phone: [
    { required: false, trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号码', trigger: 'blur' }
  ],
  role: [
    { required: true, message: '请选择角色', trigger: 'change' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度在 6 到 20 个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
      {
        validator: (rule, value, callback) => {
          if (value !== userForm.password) {
            callback(new Error('两次输入的密码不一致'))
          } else {
            callback()
          }
        },
        trigger: 'blur'
      }
  ]
})

// 计算表格最大高度
const calculateTableHeight = () => {
  const windowHeight = window.innerHeight
  const headerHeight = 80 // 页面头部高度
  const actionButtonsHeight = 55 // 操作按钮区域高度
  const searchFilterHeight = 70 // 搜索筛选区域高度
  const paginationHeight = 60 // 分页区域高度
  const padding = 0 // 移除页面内边距
  const containerPadding = 0 // 移除容器内边距
  
  const availableHeight = windowHeight - headerHeight - actionButtonsHeight - searchFilterHeight - paginationHeight - padding - containerPadding
  tableHeight.value = Math.max(300, availableHeight) // 最小高度300px，作为最大高度使用
}

// 窗口大小变化监听
const handleResize = () => {
  calculateTableHeight()
}

// 初始化
onMounted(() => {
  // 获取当前用户信息
  const storedUserInfo = localStorage.getItem('userInfo')
  if (storedUserInfo) {
    const userInfo = JSON.parse(storedUserInfo)
    currentUserId.value = userInfo.id
  }
  
  // 计算表格高度
  nextTick(() => {
    calculateTableHeight()
  })
  
  // 监听窗口大小变化
  window.addEventListener('resize', handleResize)
  
  // 加载用户列表
  loadUsers()
})

// 组件卸载时移除监听
onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})

// 加载用户列表
const loadUsers = async () => {
  try {
    loading.value = true
    users.value = await adminAPI.getUsers()
  } catch (error) {
    console.error('加载用户列表失败:', error)
    // 错误处理已在api.ts中完成
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  currentPage.value = 1
}

// 刷新
const handleRefresh = () => {
  searchKeyword.value = ''
  roleFilter.value = ''
  currentPage.value = 1
  loadUsers()
}

// 分页大小变化
const handleSizeChange = (size) => {
  pageSize.value = size
}

// 当前页码变化
const handleCurrentChange = (current) => {
  currentPage.value = current
}

// 新增用户
const handleAddUser = () => {
  isEditMode.value = false
  // 重置表单
  Object.assign(userForm, {
    id: null,
    username: '',
    email: '',
    phone: '',
    role: 'user',
    password: '',
    confirmPassword: ''
  })
  
  dialogVisible.value = true
}

// 编辑用户
const handleEditUser = (user) => {
  isEditMode.value = true
  // 填充表单
  Object.assign(userForm, {
    id: user.id,
    username: user.username,
    email: user.email,
    phone: user.phone,
    role: user.role,
    password: '',
    confirmPassword: ''
  })
  
  dialogVisible.value = true
}

// 删除用户
const handleDeleteUser = async (user) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除用户「${user.username}」吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // 发送删除请求
    await adminAPI.deleteUser(user.id)
    
    // 更新本地列表
    users.value = users.value.filter(u => u.id !== user.id)
    
    ElMessage.success('用户删除成功')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除用户失败:', error)
      // 错误处理已在api.ts中完成
    }
  }
}

// 提交表单
const handleSubmit = async () => {
  if (!userFormRef.value) return
  
  try {
    // 验证表单
    await userFormRef.value.validate()
    
    if (isEditMode.value) {
      // 编辑用户
      const { id, username, email, phone, role } = userForm
      await adminAPI.updateUser(id, {
        username,
        email,
        phone,
        role
      })
      
      // 更新本地列表
      const index = users.value.findIndex(u => u.id === id)
      if (index !== -1) {
        users.value[index] = {
          ...users.value[index],
          username,
          email,
          phone,
          role
        }
      }
      
      ElMessage.success('用户更新成功')
    } else {
      // 新增用户
      const { username, email, phone, role, password } = userForm
      const response = await adminAPI.createUser({
        username,
        email,
        phone,
        role,
        password
      })
      
      // 添加到本地列表
      users.value.push(response)
      
      ElMessage.success('用户创建成功')
    }
    
    // 关闭对话框
    dialogVisible.value = false
  } catch (error) {
    console.error('提交表单失败:', error)
    // 错误处理已在api.ts中完成
  }
}

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return ''
  
  try {
    const date = new Date(dateString)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  } catch (error) {
    return dateString
  }
}
</script>

<style scoped>
.user-management {
  padding: 0;
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
  min-width: 0;
  position: relative;
  margin: 0;
}

.page-header {
  margin-bottom: 20px;
  flex-shrink: 0;
  padding: 20px;
}

.page-header h1 {
  margin: 0 0 10px 0;
  color: #333;
}

.page-header p {
  margin: 0;
  color: #666;
}

.action-buttons {
  margin-bottom: 15px;
  flex-shrink: 0;
  display: flex;
  gap: 10px;
  padding: 0 20px;
}

.search-filter {
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  flex-shrink: 0;
  flex-wrap: wrap;
  gap: 15px;
  padding: 0 20px;
}

.table-and-pagination-container {
  display: flex;
  flex-direction: column;
  margin: 0;
  padding: 0;
  width: 100%;
  box-sizing: border-box;
}

.table-container {
  overflow: hidden;
  border-radius: 0;
  border: none;
  border-top: 1px solid #ebeef5;
  min-height: 200px;
  width: 100%;
  max-width: 100%;
  position: relative;
  box-sizing: border-box;
  contain: layout;
  display: flex;
  flex-direction: column;
  margin: 0;
  padding: 0;
  border-bottom: none;
}

.user-info {
  display: flex;
  align-items: center;
}

.pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 0 !important;
  margin-bottom: 0 !important;
  flex-shrink: 0;
  padding: 12px 20px;
  background-color: #fff;
  border-top: 1px solid #ebeef5;
  width: 100%;
  box-sizing: border-box;
}

/* 强制移除所有可能的间距 */
:deep(.el-table) + .pagination {
  margin-top: 0 !important;
}

.table-and-pagination-container > .pagination {
  margin-top: 0 !important;
}

/* 清除分页组件的所有间距 */
.table-and-pagination-container .pagination {
  margin-top: 0 !important;
  margin-bottom: 0 !important;
}

/* 表格样式优化 - 实现动态高度 */
:deep(.el-table) {
  width: 100% !important;
  max-width: 100% !important;
  table-layout: fixed !important;
  border-collapse: collapse;
  box-sizing: border-box;
  border-radius: 0;
  border-left: none;
  border-right: none;
  border-bottom: none;
  margin: 0 !important;
  padding: 0 !important;
}

/* 强制清除Element Plus表格包装器的默认间距 */
:deep(.el-table__wrapper) {
  max-width: 100%;
  overflow: hidden;
  width: 100%;
  border-radius: 0;
  margin: 0 !important;
  padding: 0 !important;
  margin-bottom: 0 !important;
}

/* 清除表格内部所有可能的间距 */
:deep(.el-scrollbar) {
  max-width: 100%;
  margin: 0 !important;
  padding: 0 !important;
}

:deep(.el-scrollbar__wrap) {
  max-width: 100%;
  overflow-x: auto;
  margin: 0 !important;
  padding: 0 !important;
}

:deep(.el-scrollbar__view) {
  margin: 0 !important;
  padding: 0 !important;
  margin-bottom: 0 !important;
  padding-bottom: 0 !important;
}

:deep(.el-table__inner-wrapper) {
  display: flex;
  flex-direction: column;
  margin: 0 !important;
  padding: 0 !important;
}

:deep(.el-table__header-wrapper) {
  overflow-x: hidden;
  max-width: 100%;
  box-sizing: border-box;
  flex-shrink: 0;
}

:deep(.el-table__body-wrapper) {
  overflow-x: auto;
  overflow-y: auto;
  max-width: 100%;
  box-sizing: border-box;
  margin: 0 !important;
  padding: 0 !important;
}

:deep(.el-table__fixed) {
  max-width: 160px;
}

/* 强制所有表格列不超出指定宽度 */
:deep(.el-table .el-table__cell) {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  box-sizing: border-box;
  max-width: 100%;
  word-break: break-all;
}

/* 确保表格头部也遵循宽度限制 */
:deep(.el-table th) {
  box-sizing: border-box;
  max-width: 100%;
}

/* 确保表格行也遵循宽度限制 */
:deep(.el-table td) {
  box-sizing: border-box;
  max-width: 100%;
}

/* 防止表格内容撑开容器 */
:deep(.el-table colgroup col) {
  box-sizing: border-box;
}

/* 强制表格内的所有元素都遵循宽度限制 */
:deep(.el-table *) {
  box-sizing: border-box;
  max-width: 100%;
}

/* 确保表格包装器不会溢出 */
:deep(.el-table__wrapper) {
  max-width: 100%;
  overflow: hidden;
  width: 100%;
  border-radius: 0;
  margin: 0 !important;
  padding: 0 !important;
}

/* 操作列特殊处理 */
:deep(.el-table__fixed-right) {
  right: 0 !important;
}

/* 确保表格整体不会横向滚动出容器 */
:deep(.el-scrollbar) {
  max-width: 100%;
}

:deep(.el-scrollbar__wrap) {
  max-width: 100%;
  overflow-x: auto;
}

/* 表格单元格内容强制换行处理 */
:deep(.el-table .cell) {
  word-wrap: break-word;
  word-break: break-all;
  white-space: normal;
  line-height: 1.5;
  padding: 8px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .user-management {
    padding: 0;
  }
  
  .page-header {
    padding: 15px;
  }
  
  .action-buttons {
    padding: 0 15px;
  }
  
  .search-filter {
    flex-direction: column;
    align-items: flex-start;
    padding: 0 15px;
    margin-bottom: 15px;
  }
  
  .search-filter .el-input,
  .search-filter .el-select,
  .search-filter .el-button {
    width: 100%;
    margin-left: 0 !important;
    margin-bottom: 10px;
  }
  
  .pagination {
    justify-content: center;
    padding: 10px 15px;
    margin-top: 0;
    background-color: #fff;
    width: 100%;
    box-sizing: border-box;
  }
  
  .table-container {
    /* 移动端也要充分利用可用空间 */
    min-height: 150px;
  }
  
  /* 移动端表格特殊优化 */
  :deep(.el-table .el-table__cell) {
    padding: 8px 4px;
    font-size: 12px;
  }
  
  /* 隐藏一些次要列 */
  :deep(.el-table-column--created_at) {
    display: none;
  }
}

@media (max-width: 480px) {
  .table-container {
    /* 小屏幕设备也要保持充分利用空间 */
    min-height: 120px;
  }
  
  .user-management {
    padding: 0;
  }
  
  .page-header {
    padding: 10px;
  }
  
  .action-buttons {
    padding: 0 10px;
  }
  
  .search-filter {
    padding: 0 10px;
    margin-bottom: 15px;
  }
  
  .pagination {
    padding: 8px 10px;
    margin-top: 0;
    background-color: #fff;
    width: 100%;
    box-sizing: border-box;
  }
  
  /* 超小屏幕表格优化 */
  :deep(.el-table .el-table__cell) {
    padding: 6px 2px;
    font-size: 11px;
  }
  
  /* 隐藏更多列 */
  :deep(.el-table-column--phone) {
    display: none;
  }
}
</style>