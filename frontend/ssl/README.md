# SSL证书配置说明

在使用`npm run build:prossl`命令时，需要在该目录下提供SSL证书文件，因为生产环境配置中引用了这些证书。

## 生成自签名证书（开发测试用）

### Windows系统（使用OpenSSL）
1. 安装OpenSSL（可通过Chocolatey或直接下载安装）
2. 打开命令提示符，导航到ssl目录
3. 运行以下命令生成私钥：
   ```
   openssl genrsa -out key.pem 2048
   ```
4. 运行以下命令生成证书：
   ```
   openssl req -new -x509 -key key.pem -out cert.pem -days 365
   ```

### Linux/Mac系统
1. 打开终端，导航到ssl目录
2. 运行以下命令：
   ```bash
   # 生成私钥
   openssl genrsa -out key.pem 2048
   # 生成证书
   openssl req -new -x509 -key key.pem -out cert.pem -days 365
   ```

## 使用正式证书

如果您有正式的SSL证书，请将私钥保存为`key.pem`，证书保存为`cert.pem`，并放置在此目录下。

## 注意事项
- 自签名证书仅用于开发和测试环境
- 生产环境应使用由可信证书颁发机构（CA）签发的证书
- 确保证书文件权限设置正确，避免未授权访问