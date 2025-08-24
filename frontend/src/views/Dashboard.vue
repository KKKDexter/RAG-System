<template>
  <div class="dashboard">
    <div class="dashboard-header">
      <h1>数据分析看板</h1>
      <p>欢迎回来，{{ userInfo?.username }}！以下是您的系统使用概览</p>
    </div>
    
    <!-- 统计卡片 -->
    <div class="stats-cards">
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon">
            <el-icon><Document /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-number">{{ documentCount }}</div>
            <div class="stat-label">已上传文档</div>
          </div>
        </div>
      </el-card>
      
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon">
            <el-icon><Message /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-number">{{ qaCount }}</div>
            <div class="stat-label">问答次数</div>
          </div>
        </div>
      </el-card>
      
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon">
            <el-icon><Clock /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-number">{{ activeDays }}</div>
            <div class="stat-label">活跃天数</div>
          </div>
        </div>
      </el-card>
      
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon">
            <el-icon><PieChart /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-number">{{ usageRate }}%</div>
            <div class="stat-label">本周使用率</div>
          </div>
        </div>
      </el-card>
    </div>
    
    <!-- 图表区域 -->
    <div class="charts-section">
      <el-card class="chart-card">
        <template #header>
          <div class="card-header">
            <span>问答趋势分析</span>
            <el-select v-model="timeRange" placeholder="选择时间范围" size="small">
              <el-option label="最近7天" value="7d" />
              <el-option label="最近30天" value="30d" />
              <el-option label="最近90天" value="90d" />
            </el-select>
          </div>
        </template>
        <div class="chart-container">
          <!-- 这里将放置图表组件 -->
          <div class="chart-placeholder">
            <el-icon><PieChart /></el-icon>
            <p>问答趋势图表区域</p>
          </div>
        </div>
      </el-card>
      
      <el-card class="chart-card">
        <template #header>
          <div class="card-header">
            <span>文档类型分布</span>
          </div>
        </template>
        <div class="chart-container">
          <!-- 这里将放置图表组件 -->
          <div class="chart-placeholder">
            <el-icon><PieChart /></el-icon>
            <p>文档类型分布图区域</p>
          </div>
        </div>
      </el-card>
    </div>
    
    <!-- 最近活动 -->
    <el-card class="recent-activities">
      <template #header>
        <div class="card-header">
          <span>最近活动</span>
        </div>
      </template>
      <el-table :data="recentActivities" style="width: 100%">
        <el-table-column prop="type" label="活动类型" width="120" />
        <el-table-column prop="description" label="描述" />
        <el-table-column prop="time" label="时间" width="180" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
<<<<<<< HEAD
import { authAPI } from '../utils/api'
=======
import { authAPI, statsAPI } from '../utils/api'
>>>>>>> main

// 用户信息
const userInfo = ref(null)

// 统计数据
const documentCount = ref(0)
const qaCount = ref(0)
const activeDays = ref(0)
const usageRate = ref(0)
const timeRange = ref('7d')

// 最近活动数据
const recentActivities = ref([
  { type: '问答', description: '询问了关于系统架构的问题', time: '2023-07-15 14:30' },
  { type: '上传', description: '上传了文档《RAG技术白皮书》', time: '2023-07-14 10:15' },
  { type: '问答', description: '询问了关于向量数据库的问题', time: '2023-07-13 16:45' },
  { type: '登录', description: '用户登录系统', time: '2023-07-12 09:20' }
])

// 初始化数据
onMounted(() => {
  // 使用API获取用户信息
  loadUserInfo()
  
  // 加载统计数据
  loadStatistics()
  
  // 加载最近活动
  loadRecentActivities()
})

// 加载用户信息
const loadUserInfo = async () => {
  try {
    userInfo.value = await authAPI.getCurrentUser()
  } catch (error) {
    console.error('加载用户信息失败:', error)
    // 错误处理已在api.ts中完成
  }
}

// 加载统计数据
const loadStatistics = async () => {
  try {
    // 模拟API请求延迟
    await new Promise(resolve => setTimeout(resolve, 500))
    
    // 获取真实统计数据 - 使用模拟数据代替不存在的API
    const stats = {
      documentCount: 12,
      qaCount: 45,
      activeDays: 18,
      usageRate: 75
    }
    
    documentCount.value = stats.documentCount
    qaCount.value = stats.qaCount
    activeDays.value = stats.activeDays
    usageRate.value = stats.usageRate
  } catch (error) {
    console.error('加载统计数据失败:', error)
    // 错误处理已在api.ts中完成
    // 使用默认值
    documentCount.value = 12
    qaCount.value = 45
    activeDays.value = 18
    usageRate.value = 75
  }
}

// 加载最近活动
const loadRecentActivities = async () => {
  try {
    // 模拟API请求延迟
    await new Promise(resolve => setTimeout(resolve, 800))
    
    // 使用默认数据代替不存在的API
    // 实际项目中可能需要从服务器获取
  } catch (error) {
    console.error('加载最近活动失败:', error)
    // 错误处理已在api.ts中完成
    // 保持原有默认数据
  }
}
</script>

<style scoped>
.dashboard {
  padding: 20px;
}

.dashboard-header {
  margin-bottom: 30px;
}

.dashboard-header h1 {
  margin: 0 0 10px 0;
  color: #333;
}

.dashboard-header p {
  margin: 0;
  color: #666;
}

/* 统计卡片样式 */
.stats-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.stat-card {
  height: 100%;
}

.stat-content {
  display: flex;
  align-items: center;
  padding: 20px;
}

.stat-icon {
  font-size: 32px;
  color: #409eff;
  margin-right: 20px;
}

.stat-info {
  flex: 1;
}

.stat-number {
  font-size: 24px;
  font-weight: bold;
  color: #333;
}

.stat-label {
  font-size: 14px;
  color: #666;
  margin-top: 5px;
}

/* 图表区域样式 */
.charts-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.chart-card {
  height: 300px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-container {
  height: calc(100% - 50px);
  display: flex;
  align-items: center;
  justify-content: center;
}

.chart-placeholder {
  text-align: center;
  color: #909399;
}

.chart-placeholder .el-icon {
  font-size: 48px;
  margin-bottom: 10px;
}

/* 最近活动表格样式 */
.recent-activities {
  margin-bottom: 20px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .stats-cards {
    grid-template-columns: 1fr;
  }
  
  .charts-section {
    grid-template-columns: 1fr;
  }
  
  .chart-card {
    height: 250px;
  }
}
</style>