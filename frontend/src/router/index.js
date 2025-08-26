import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import MainLayout from '../components/MainLayout.vue'
import Dashboard from '../views/Dashboard.vue'
import DocumentManagement from '../views/DocumentManagement.vue'
import QASystem from '../views/QASystem.vue'
import UserManagement from '../views/UserManagement.vue'
import SystemSettings from '../views/SystemSettings.vue'
import LLMManagement from '../views/LLMManagement.vue'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: {
      requiresAuth: false
    }
  },
  {
    path: '/',
    component: MainLayout,
    meta: {
      requiresAuth: true
    },
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: Dashboard
      },
      {
        path: 'documents',
        name: 'DocumentManagement',
        component: DocumentManagement
      },
      {
        path: 'qa',
        name: 'QASystem',
        component: QASystem
      },
      {
        path: 'admin/users',
        name: 'UserManagement',
        component: UserManagement,
        meta: {
          requiresAdmin: true
        }
      },
      {
        path: 'admin/settings',
        name: 'SystemSettings',
        component: SystemSettings,
        meta: {
          requiresAdmin: true
        }
      },
      {
        path: 'admin/llm',
        name: 'LLMManagement',
        component: LLMManagement,
        meta: {
          requiresAdmin: true
        }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  const userInfo = localStorage.getItem('userInfo')
  const user = userInfo ? JSON.parse(userInfo) : null
  
  // 检查是否需要认证
  if (to.meta.requiresAuth && !token) {
    next({ name: 'Login' })
    return
  }
  
  // 检查是否需要管理员权限
  if (to.meta.requiresAdmin && (!user || user.role !== 'admin')) {
    next({ name: 'Dashboard' })
    return
  }
  
  next()
})

export default router