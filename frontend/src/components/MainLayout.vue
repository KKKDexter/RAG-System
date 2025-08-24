<template>
  <div class="main-layout">
    <!-- 侧边栏导航 -->
    <aside class="sidebar" :class="{ collapsed: isSidebarCollapsed }">
      <div class="sidebar-header">
        <h2 class="logo" v-if="!isSidebarCollapsed">RAG系统</h2>
        <h2 class="logo-collapsed" v-else>R</h2>
        <button class="toggle-btn" @click="toggleSidebar">
          <el-icon>{{ isSidebarCollapsed ? 'Right' : 'Left' }}</el-icon>
        </button>
      </div>
      
      <nav class="menu">
        <el-menu
          :default-active="activeMenuItem"
          class="el-menu-vertical"
          @select="handleMenuSelect"
        >
          <el-menu-item index="Dashboard">
            <el-icon><PieChart /></el-icon>
            <span v-if="!isSidebarCollapsed">数据分析看板</span>
          </el-menu-item>
          
          <el-menu-item index="DocumentManagement">
            <el-icon><Document /></el-icon>
            <span v-if="!isSidebarCollapsed">知识库管理</span>
          </el-menu-item>
          
          <el-menu-item index="QASystem">
            <el-icon><Message /></el-icon>
            <span v-if="!isSidebarCollapsed">问答系统</span>
          </el-menu-item>
          
          <!-- 管理员菜单项 -->
          <el-sub-menu index="Admin" v-if="userInfo && userInfo.role === 'admin'">
            <template #title>
              <el-icon><Setting /></el-icon>
              <span v-if="!isSidebarCollapsed">系统管理</span>
            </template>
            <el-menu-item index="UserManagement">
              <el-icon><User /></el-icon>
              <span v-if="!isSidebarCollapsed">用户权限管理</span>
            </el-menu-item>
            <el-menu-item index="SystemSettings">
              <el-icon><Cog /></el-icon>
              <span v-if="!isSidebarCollapsed">RAG系统管理</span>
            </el-menu-item>
          </el-sub-menu>
        </el-menu>
      </nav>
    </aside>
    
    <!-- 主内容区域 -->
    <main class="main-content">
      <!-- 顶部导航栏 -->
      <header class="top-nav">
        <div class="nav-left">
          <button class="mobile-menu-btn" @click="toggleSidebar">
            <el-icon><Menu /></el-icon>
          </button>
        </div>
        
        <div class="nav-right">
          <el-dropdown trigger="hover" @command="handleDropdownCommand">
            <span class="user-info">
              <el-avatar class="avatar">{{ userInfo?.username?.charAt(0).toUpperCase() }}</el-avatar>
              <span class="username" v-if="userInfo">{{ userInfo.username }}</span>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人信息</el-dropdown-item>
                <el-dropdown-item command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>
      
      <!-- 内容区域 -->
      <div class="content">
        <router-view />
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { UserOut } from '../types/user'
import { authAPI } from '../utils/api'

const router = useRouter()
const isSidebarCollapsed = ref(false)
const userInfo = ref<UserOut | null>(null)

// 计算当前激活的菜单项
const activeMenuItem = computed(() => {
  return router.currentRoute.value.name as string || 'Dashboard'
})

// 切换侧边栏折叠状态
const toggleSidebar = () => {
  isSidebarCollapsed.value = !isSidebarCollapsed.value
}

// 处理菜单选择
const handleMenuSelect = (index: string) => {
  router.push({ name: index })
}

// 处理下拉菜单命令
const handleDropdownCommand = (command: string) => {
  if (command === 'logout') {
    // 退出登录，清除本地存储
    localStorage.removeItem('token')
    localStorage.removeItem('userInfo')
    router.push({ name: 'Login' })
    ElMessage.success('退出登录成功')
  } else if (command === 'profile') {
    // 跳转到个人信息页面（如果有的话）
    ElMessage.info('个人信息功能待实现')
  }
}

// 初始化时加载用户信息
onMounted(() => {
  const storedUserInfo = localStorage.getItem('userInfo')
  if (storedUserInfo) {
    userInfo.value = JSON.parse(storedUserInfo)
  }
  
  // 尝试从服务器获取最新的用户信息
  fetchUserInfo()
})

// 从服务器获取用户信息
const fetchUserInfo = async () => {
  try {
    userInfo.value = await authAPI.getCurrentUser()
    localStorage.setItem('userInfo', JSON.stringify(userInfo.value))
  } catch (error) {
    console.error('获取用户信息失败:', error)
    // 错误处理已在api.ts中完成，但仍需清除本地存储并重定向
    localStorage.removeItem('token')
    localStorage.removeItem('userInfo')
    router.push({ name: 'Login' })
  }
}
</script>

<style scoped>
.main-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

/* 侧边栏样式 */
.sidebar {
  width: 240px;
  background-color: #2c3e50;
  color: white;
  display: flex;
  flex-direction: column;
  transition: width 0.3s ease;
  height: 100vh;
  position: fixed;
  left: 0;
  top: 0;
  z-index: 1000;
}

.sidebar.collapsed {
  width: 60px;
}

.sidebar-header {
  padding: 20px 15px;
  border-bottom: 1px solid #34495e;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.logo {
  font-size: 18px;
  font-weight: bold;
  margin: 0;
}

.logo-collapsed {
  font-size: 18px;
  font-weight: bold;
  margin: 0;
  text-align: center;
}

.toggle-btn {
  background: none;
  border: none;
  color: white;
  cursor: pointer;
  padding: 5px;
  border-radius: 4px;
}

.toggle-btn:hover {
  background-color: #34495e;
}

.menu {
  flex: 1;
  padding-top: 20px;
}

.el-menu-vertical {
  background-color: transparent;
  border-right: none;
}

.el-menu-vertical .el-menu-item,
.el-menu-vertical .el-sub-menu__title {
  color: #ecf0f1;
  height: 48px;
  line-height: 48px;
}

.el-menu-vertical .el-menu-item:hover,
.el-menu-vertical .el-sub-menu__title:hover {
  background-color: #34495e;
}

.el-menu-vertical .el-menu-item.is-active {
  background-color: #1abc9c;
  color: white;
}

/* 主内容区域样式 */
.main-content {
  flex: 1;
  margin-left: 240px;
  transition: margin-left 0.3s ease;
  display: flex;
  flex-direction: column;
  height: 100vh;
}

.sidebar.collapsed + .main-content {
  margin-left: 60px;
}

/* 顶部导航栏样式 */
.top-nav {
  height: 60px;
  background-color: white;
  border-bottom: 1px solid #e1e5e9;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.mobile-menu-btn {
  display: none;
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
}

.user-info {
  display: flex;
  align-items: center;
  cursor: pointer;
}

.avatar {
  margin-right: 10px;
}

/* 内容区域样式 */
.content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  background-color: #f5f7fa;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .sidebar {
    transform: translateX(-100%);
  }
  
  .sidebar.collapsed {
    transform: translateX(0);
    width: 240px;
  }
  
  .main-content {
    margin-left: 0;
  }
  
  .mobile-menu-btn {
    display: block;
  }
}
</style>