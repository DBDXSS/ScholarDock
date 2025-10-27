@echo off
chcp 65001 > nul
echo ===============================================
echo 🚀 Google Scholar Spider - 一键环境安装脚本
echo ===============================================
echo.

REM ===========================================
REM 配置选项 - 可根据需要修改
REM ===========================================
REM Python 版本配置
set PYTHON_VERSION=3.10.11
set PYTHON_DOWNLOAD_URL=https://www.python.org/ftp/python/3.10.11/python-3.10.11-amd64.exe

REM Node.js 版本配置
set NODEJS_VERSION=20.10.0
set NODEJS_DOWNLOAD_URL=https://nodejs.org/dist/v20.10.0/node-v20.10.0-x64.msi

REM 国内镜像源配置 (设置为1启用国内源，0使用官方源)
set USE_CHINA_MIRROR=1

REM Python 路径配置 (留空使用系统默认路径，或设置已安装的Python路径)
REM 例如: set CUSTOM_PYTHON_PATH=C:\Python310
REM 或者: set CUSTOM_PYTHON_PATH=C:\Users\用户名\AppData\Local\Programs\Python\Python310
set CUSTOM_PYTHON_PATH=

REM 镜像源地址配置
if %USE_CHINA_MIRROR%==1 (
    set PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
    set NPM_REGISTRY=https://registry.npmmirror.com
    set PYTHON_DOWNLOAD_URL=https://npm.taobao.org/mirrors/python/3.10.11/python-3.10.11-amd64.exe
    set NODEJS_DOWNLOAD_URL=https://npm.taobao.org/mirrors/node/v20.10.0/node-v20.10.0-x64.msi
) else (
    set PIP_INDEX_URL=https://pypi.org/simple
    set NPM_REGISTRY=https://registry.npmjs.org
)

echo 🔧 配置信息：
echo    Python 版本: %PYTHON_VERSION%
echo    使用国内镜像: %USE_CHINA_MIRROR%
if defined CUSTOM_PYTHON_PATH echo    Python 路径: %CUSTOM_PYTHON_PATH%
echo    pip 源: %PIP_INDEX_URL%
echo    npm 源: %NPM_REGISTRY%
echo.

REM 检查管理员权限
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ⚠️  需要管理员权限来安装某些组件
    echo 💡 请右键点击此文件，选择"以管理员身份运行"
    pause
    exit /b 1
)

echo 📋 开始检查和安装所需环境...
echo.

REM ===========================================
REM 检查并安装 Python
REM ===========================================
echo 🐍 检查 Python 环境...

REM 如果设置了自定义路径，先检查该路径
if defined CUSTOM_PYTHON_PATH (
    if exist "%CUSTOM_PYTHON_PATH%\python.exe" (
        set "PATH=%CUSTOM_PYTHON_PATH%;%CUSTOM_PYTHON_PATH%\Scripts;%PATH%"
        echo ✅ 使用已配置的 Python 路径: %CUSTOM_PYTHON_PATH%
        
        REM 获取该路径下的Python版本
        for /f "tokens=2" %%i in ('"%CUSTOM_PYTHON_PATH%\python.exe" --version 2^>^&1') do set CURRENT_PYTHON_VERSION=%%i
        echo ✅ Python 已配置 (版本: %CURRENT_PYTHON_VERSION%)
        goto skip_python_install
    ) else (
        echo ⚠️  自定义 Python 路径不存在: %CUSTOM_PYTHON_PATH%
        echo 💡 将检查系统 Python 或进行新安装
    )
)

:check_python_version
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python 未安装
    echo 📥 正在下载 Python %PYTHON_VERSION%...
    echo 🌐 下载源: %PYTHON_DOWNLOAD_URL%
    
    REM 下载 Python 安装程序
    powershell -Command "Invoke-WebRequest -Uri '%PYTHON_DOWNLOAD_URL%' -OutFile 'python-installer.exe'"
    
    if %errorlevel% neq 0 (
        echo ❌ Python 下载失败，请检查网络连接
        pause
        exit /b 1
    )
    
    REM 构建安装参数
    set INSTALL_ARGS=/quiet InstallAllUsers=1 PrependPath=1 Include_test=0
    if defined CUSTOM_PYTHON_PATH (
        set INSTALL_ARGS=%INSTALL_ARGS% TargetDir="%CUSTOM_PYTHON_PATH%"
    )
    
    REM 静默安装 Python
    echo 🔧 正在安装 Python（这可能需要几分钟）...
    python-installer.exe %INSTALL_ARGS%
    
    REM 等待安装完成
    timeout /t 30 /nobreak > nul
    
    REM 刷新环境变量
    call refreshenv.cmd >nul 2>&1
    
    REM 如果设置了自定义路径，更新 PATH
    if defined CUSTOM_PYTHON_PATH (
        set "PATH=%CUSTOM_PYTHON_PATH%;%CUSTOM_PYTHON_PATH%\Scripts;%PATH%"
    )
    
    REM 删除安装程序
    del python-installer.exe >nul 2>&1
    
    echo ✅ Python 安装完成
) else (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do set CURRENT_PYTHON_VERSION=%%i
    echo ✅ Python 已安装 (版本: %CURRENT_PYTHON_VERSION%)
)

:skip_python_install

REM ===========================================
REM 检查并安装 Node.js
REM ===========================================
echo.
echo 📦 检查 Node.js 环境...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js 未安装
    echo 📥 正在下载 Node.js %NODEJS_VERSION%...
    echo 🌐 下载源: %NODEJS_DOWNLOAD_URL%
    
    REM 下载 Node.js 安装程序
    powershell -Command "Invoke-WebRequest -Uri '%NODEJS_DOWNLOAD_URL%' -OutFile 'nodejs-installer.msi'"
    
    if %errorlevel% neq 0 (
        echo ❌ Node.js 下载失败，请检查网络连接
        pause
        exit /b 1
    )
    
    REM 静默安装 Node.js
    echo 🔧 正在安装 Node.js（这可能需要几分钟）...
    msiexec /i nodejs-installer.msi /quiet /norestart
    
    REM 等待安装完成
    timeout /t 30 /nobreak > nul
    
    REM 刷新环境变量
    call refreshenv.cmd >nul 2>&1
    
    REM 删除安装程序
    del nodejs-installer.msi >nul 2>&1
    
    echo ✅ Node.js 安装完成
) else (
    for /f "tokens=1" %%i in ('node --version 2^>^&1') do set CURRENT_NODE_VERSION=%%i
    echo ✅ Node.js 已安装 (版本: %CURRENT_NODE_VERSION%)
)

REM ===========================================
REM 检查并安装 npm
REM ===========================================
echo.
echo 📦 检查 npm...
npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ npm 未找到，请重新安装 Node.js
    pause
    exit /b 1
) else (
    for /f "tokens=1" %%i in ('npm --version 2^>^&1') do set CURRENT_NPM_VERSION=%%i
    echo ✅ npm 已安装 (版本: %CURRENT_NPM_VERSION%)
)

REM 配置 npm 镜像源
echo 🔧 配置 npm 镜像源...
npm config set registry %NPM_REGISTRY%
echo ✅ npm 镜像源已设置为: %NPM_REGISTRY%

REM ===========================================
REM 安装 Python 依赖
REM ===========================================
echo.
echo 🐍 安装 Python 依赖包...
echo 📍 切换到 backend 目录...
cd backend

echo 🔧 升级 pip 并配置镜像源...
REM 使用配置的Python路径或系统Python
if defined CUSTOM_PYTHON_PATH (
    "%CUSTOM_PYTHON_PATH%\python.exe" -m pip install --upgrade pip -i %PIP_INDEX_URL%
) else (
    python -m pip install --upgrade pip -i %PIP_INDEX_URL%
)

echo 📦 安装 requirements.txt 中的依赖...
echo 🌐 使用 pip 源: %PIP_INDEX_URL%
if defined CUSTOM_PYTHON_PATH (
    "%CUSTOM_PYTHON_PATH%\Scripts\pip.exe" install -r requirements.txt -i %PIP_INDEX_URL%
) else (
    pip install -r requirements.txt -i %PIP_INDEX_URL%
)

if %errorlevel% neq 0 (
    echo ❌ Python 依赖安装失败
    echo 💡 尝试使用官方源重新安装...
    if defined CUSTOM_PYTHON_PATH (
        "%CUSTOM_PYTHON_PATH%\Scripts\pip.exe" install -r requirements.txt
    ) else (
        pip install -r requirements.txt
    )
    if %errorlevel% neq 0 (
        echo ❌ Python 依赖安装仍然失败
        pause
        exit /b 1
    )
)

echo ✅ Python 依赖安装完成
cd ..

REM ===========================================
REM 安装 JavaScript 依赖
REM ===========================================
echo.
echo 📦 安装 JavaScript 依赖包...
echo 📍 切换到 frontend 目录...
cd frontend

echo 🔧 安装 npm 依赖...
echo 🌐 使用 npm 源: %NPM_REGISTRY%
npm install

if %errorlevel% neq 0 (
    echo ❌ JavaScript 依赖安装失败
    echo 💡 尝试清理缓存后重新安装...
    npm cache clean --force
    npm install
    if %errorlevel% neq 0 (
        echo ❌ JavaScript 依赖安装仍然失败
        pause
        exit /b 1
    )
)

echo ✅ JavaScript 依赖安装完成
cd ..

REM ===========================================
REM 创建必要目录
REM ===========================================
echo.
echo 📁 创建必要目录...
if not exist "data" mkdir data
if not exist "logs" mkdir logs
if not exist "downloads" mkdir downloads
echo ✅ 目录创建完成

REM ===========================================
REM 创建配置文件
REM ===========================================
echo.
echo 📝 创建配置文件...
echo # Python 和 pip 配置 > config.txt
echo PYTHON_PATH=%CUSTOM_PYTHON_PATH% >> config.txt
echo PIP_INDEX_URL=%PIP_INDEX_URL% >> config.txt
echo NPM_REGISTRY=%NPM_REGISTRY% >> config.txt
echo USE_CHINA_MIRROR=%USE_CHINA_MIRROR% >> config.txt
echo ✅ 配置已保存到 config.txt

REM ===========================================
REM 安装完成
REM ===========================================
echo.
echo ===============================================
echo ✨ 环境安装完成！
echo ===============================================
echo.
echo 🎯 已安装的组件：
if defined CURRENT_PYTHON_VERSION (
    echo    • Python %CURRENT_PYTHON_VERSION%
) else (
    echo    • Python %PYTHON_VERSION%
)
if defined CURRENT_NODE_VERSION (
    echo    • Node.js %CURRENT_NODE_VERSION%
) else (
    echo    • Node.js %NODEJS_VERSION%
)
if defined CURRENT_NPM_VERSION (
    echo    • npm %CURRENT_NPM_VERSION%
)
echo    • 所有 Python 依赖包 (使用源: %PIP_INDEX_URL%)
echo    • 所有 JavaScript 依赖包 (使用源: %NPM_REGISTRY%)
echo.
if defined CUSTOM_PYTHON_PATH (
    echo 📍 Python 安装路径: %CUSTOM_PYTHON_PATH%
    echo.
)
echo 🚀 现在你可以运行以下命令启动服务：
echo    • run.bat          - 标准模式启动
echo    • run-background.bat - 后台模式启动
echo.
echo 🛑 停止服务：
echo    • stop.bat         - 停止所有服务
echo.
echo 📋 查看日志：
echo    • tail-logs.bat    - 实时查看日志
echo.
echo 📝 配置信息已保存到 config.txt 文件中
echo.
pause