import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import localConfig from './config/local.js'
import devConfig from './config/dev.js'
import prodConfig from './config/prod.js'

// 根据不同环境选择对应的配置
const getConfigByMode = (mode) => {
  switch (mode) {
    case 'localdev':
      return localConfig
    case 'production':
      return prodConfig
    case 'development':
    case 'dev':
    default:
      return devConfig
  }
}

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const envConfig = getConfigByMode(mode)
  
  // 定义全局环境变量，供前端代码使用
  const define = {
    'process.env.NODE_ENV': JSON.stringify(mode),
    'import.meta.env.VITE_ENV': JSON.stringify(mode)
  }
  
  return {
    plugins: [vue()],
    ...envConfig,
    define
  }
})