export default {
  // 服务器配置
  server: {
    port: 3000,
    // 在local环境下不需要代理到后端，因为我们会使用模拟数据
  },
  
  // 构建配置
  build: {
    outDir: 'dist-local',
    sourcemap: true
  },
  
  // 环境标识，用于前端代码判断
  environment: 'local'
}