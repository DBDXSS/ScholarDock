# ScholarDock - Windows 安装指南

本文档专门为Windows用户提供详细的安装和启动指南。

## 📋 系统要求

- Windows 10 或更高版本
- Python 3.8 或更高版本
- Node.js 16 或更高版本
- Chrome 或 Edge 浏览器（用于Selenium后备功能）

## 🛠️ 安装步骤

### 1. 安装 Python

如果您还没有安装Python，请按照以下步骤：

1. 访问 [Python官网](https://www.python.org/downloads/windows/)
2. 下载最新的Python 3.8+版本
3. 运行安装程序时，**务必勾选 "Add Python to PATH"**
4. 验证安装：
   ```cmd
   python --version
   pip --version
   ```

### 2. 安装 Node.js

1. 访问 [Node.js官网](https://nodejs.org/)
2. 下载LTS版本（推荐）
3. 运行安装程序，按默认设置安装
4. 验证安装：
   ```cmd
   node --version
   npm --version
   ```

### 3. 克隆项目

打开命令提示符（CMD）或PowerShell：

```cmd
git clone <your-repository-url>
cd scholardock
```

### 4. 设置后端

```cmd
cd backend
pip install -r requirements.txt
```

如果遇到权限问题，可以尝试：
```cmd
pip install -r requirements.txt --user
```

创建环境变量文件（可选）：
```cmd
echo DEBUG=false > .env
echo DATABASE_URL=sqlite+aiosqlite:///./data/scholar.db >> .env
echo USE_SELENIUM_FALLBACK=true >> .env
```

### 5. 设置前端

```cmd
cd ..\frontend
npm install
```

如果npm安装很慢，可以使用国内镜像：
```cmd
npm config set registry https://registry.npmmirror.com
npm install
```

## 🚀 启动应用

### 方法一：使用Python脚本（推荐）

在项目根目录下：
```cmd
python start.py
```

这将自动启动后端和前端服务。

**注意**：Windows不支持`.sh`脚本文件，请使用Python脚本启动。

### 方法二：手动启动

**启动后端** - 在第一个命令提示符窗口中：
```cmd
cd backend
python run.py
```

**启动前端** - 在第二个命令提示符窗口中：
```cmd
cd frontend
npm run dev
```

### 服务地址

启动成功后，您可以访问：
- 前端应用：`http://localhost:3000`
- 后端API：`http://localhost:8001`
- API文档：`http://localhost:8001/docs`

## 🛑 停止应用

- 如果使用`python start.py`启动，按 `Ctrl+C` 停止
- 如果手动启动，在每个命令提示符窗口中按 `Ctrl+C`

**注意**：Windows不支持`./stop.sh`脚本，请使用`Ctrl+C`组合键停止服务。

## 🔧 常见问题解决

### Python相关问题

**问题1：'python' 不是内部或外部命令**
- 解决：重新安装Python，确保勾选"Add Python to PATH"
- 或者使用完整路径：`C:\Users\YourName\AppData\Local\Programs\Python\Python39\python.exe`

**问题2：pip安装包失败**
- 解决：升级pip：`python -m pip install --upgrade pip`
- 或使用国内镜像：`pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple`

### Node.js相关问题

**问题1：npm安装很慢**
- 解决：使用国内镜像：
  ```cmd
  npm config set registry https://registry.npmmirror.com
  npm install
  ```

**问题2：权限错误**
- 解决：以管理员身份运行命令提示符

### 端口占用问题

**问题：端口3000或8001被占用**
- 解决：查找并结束占用进程：
  ```cmd
  netstat -ano | findstr :3000
  taskkill /PID <进程ID> /F
  ```

### Chrome/Edge驱动问题

**问题：Selenium无法启动浏览器**
- 解决：确保已安装Chrome或Edge浏览器
- 系统会自动下载对应的驱动程序

## 📁 Windows特定的目录结构

```
C:\Users\YourName\scholardock\
├── backend\
│   ├── data\               # 数据库文件目录
│   ├── downloads\          # PDF下载目录
│   └── ...
├── frontend\
│   ├── node_modules\       # npm依赖包
│   └── ...
└── logs\                   # 日志文件目录
```

## 🎯 使用建议

1. **首次使用**：建议先搜索少量结果（如10-20篇）测试功能
2. **大量搜索**：如需搜索大量文献，建议分批进行，避免被Google Scholar限制
3. **PDF下载**：下载的PDF文件默认保存在`downloads`目录中
4. **数据备份**：重要的搜索结果会保存在`data\scholar.db`中，建议定期备份

## 📞 技术支持

如果遇到其他问题，请：
1. 检查防火墙设置，确保允许Python和Node.js访问网络
2. 确保网络连接正常，能够访问Google Scholar
3. 查看控制台输出的错误信息，通常会提供解决线索

---

**注意**：本工具仅供学术研究使用，请遵守Google Scholar的使用条款。