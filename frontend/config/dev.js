// 开发环境配置
export default {
  // 服务器配置
  server: {
    port: 3000,
    host: '0.0.0.0', // 添加host参数，使服务器监听所有网络接口
    proxy: {
      '/api': {
        target: 'http://192.168.1.11:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  },
  
  // 构建配置
  build: {
    outDir: 'dist',
    sourcemap: false
  }
}