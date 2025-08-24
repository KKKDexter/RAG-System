// 生产环境SSL配置
export default {
  // 服务器配置
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    },
    // SSL配置
    https: {
      key: './ssl/key.pem',
      cert: './ssl/cert.pem'
    }
  },
  
  // 构建配置
  build: {
    outDir: 'dist',
    sourcemap: false,
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true
      }
    }
  }
}