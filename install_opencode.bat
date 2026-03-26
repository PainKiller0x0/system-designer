@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

echo ==========================================
echo System Designer - OpenCode 安装脚本
echo ==========================================

set "SCRIPT_DIR=%~dp0"

echo.
echo Step 1: 检查依赖...

:: 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.10+
    pause
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [✓] Python: %PYTHON_VERSION%

:: 检查 Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo [警告] 未找到 Node.js，如需使用 OpenCode CLI 请先安装
) else (
    for /f "tokens=*" %%i in ('node --version 2^>^&1') do set NODE_VERSION=%%i
    echo [✓] Node.js: !NODE_VERSION!
)

echo.
echo Step 2: 安装 Python 依赖...

:: 创建虚拟环境
set "VENV_DIR=%SCRIPT_DIR%src\subagent\system_designer_beta\.venv"
if not exist "%VENV_DIR%" (
    echo 创建虚拟环境...
    python -m venv "%VENV_DIR%"
)

:: 激活虚拟环境并安装依赖
call "%VENV_DIR%\Scripts\activate.bat"
pip install -r "%SCRIPT_DIR%src\subagent\system_designer_beta\requirements.txt"

echo [✓] Python 依赖安装完成

echo.
echo Step 3: 配置环境变量...

set "ENV_FILE=%SCRIPT_DIR%src\subagent\system_designer_beta\.env"
set "ENV_EXAMPLE=%SCRIPT_DIR%src\subagent\system_designer_beta\.env.example"

if not exist "%ENV_FILE%" (
    echo 创建 .env 文件...
    copy "%ENV_EXAMPLE%" "%ENV_FILE%"
    echo [警告] 请编辑 %ENV_FILE% 并填入你的 ANTHROPIC_API_KEY
) else (
    echo [✓] .env 文件已存在
)

echo.
echo Step 4: 创建必要的目录...

if not exist "%SCRIPT_DIR%docs\reference" mkdir "%SCRIPT_DIR%docs\reference"
if not exist "%SCRIPT_DIR%data\images" mkdir "%SCRIPT_DIR%data\images"
if not exist "%SCRIPT_DIR%data\sessions" mkdir "%SCRIPT_DIR%data\sessions"
if not exist "%SCRIPT_DIR%data\test" mkdir "%SCRIPT_DIR%data\test"

echo [✓] 目录创建完成

echo.
echo Step 5: 配置 OpenCode...

:: 检查是否已安装 OpenCode
opencode --version >nul 2>&1
if errorlevel 1 (
    echo [警告] 未找到 OpenCode CLI
    echo 请运行: npm install -g opencode
) else (
    echo [✓] OpenCode 已安装
    
    :: 创建 OpenCode 配置目录
    set "OPENCODE_CONFIG_DIR=%USERPROFILE%\.opencode"
    if not exist "!OPENCODE_CONFIG_DIR!\skills" mkdir "!OPENCODE_CONFIG_DIR!\skills"
    
    :: 复制 Skill 文件
    echo 安装 Skill 到 OpenCode...
    copy "%SCRIPT_DIR%SKILL.md" "!OPENCODE_CONFIG_DIR!\skills\system-designer.md" >nul
    copy "%SCRIPT_DIR%OPENCODE.md" "!OPENCODE_CONFIG_DIR!\skills\system-designer-opencode.md" >nul
    
    echo [✓] Skill 已安装到 OpenCode
)

echo.
echo ==========================================
echo [✓] 安装完成！
echo ==========================================
echo.
echo 下一步：
echo 1. 编辑 %ENV_FILE%，填入你的 ANTHROPIC_API_KEY
echo 2. 启动 OpenCode: opencode
echo 3. 说「帮我设计一个XX系统」开始使用
echo.
echo 详细使用说明请参考 README.md
echo.
pause