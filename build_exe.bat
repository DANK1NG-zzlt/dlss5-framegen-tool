@echo off
chcp 65001 >nul
title DLSS 5 Frame Gen Tool - Build EXE
echo ============================================
echo   DLSS 5 + 帧生成工具 - 一键打包 EXE
echo   （内置 OptiScaler v0.9.4 完整版，无需联网下载）
echo ============================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [X] 未检测到 Python，请先安装 Python 3.10+ 并勾选 Add to PATH
    pause
    exit /b 1
)

echo [1/4] 安装依赖...
python -m pip install --upgrade pip
python -m pip install customtkinter pillow pyinstaller py7zr wmi requests
if errorlevel 1 (
    echo [X] 依赖安装失败
    pause
    exit /b 1
)

echo.
echo [2/4] 检查 OptiScaler 完整包...
if not exist "OptiScaler_v0.9.4_full.7z" (
    echo     未找到本地包，正在从 GitHub 下载（约 55MB）...
    python -c "import urllib.request; urllib.request.urlretrieve('https://github.com/optiscaler/OptiScaler/releases/download/v0.9.4/Optiscaler_0.9.4-final.20260718._MM.7z', 'OptiScaler_v0.9.4_full.7z')"
    if errorlevel 1 (
        echo [X] OptiScaler 下载失败，请手动下载放到当前目录
        pause
        exit /b 1
    )
) else (
    echo     ✓ 已找到 OptiScaler_v0.9.4_full.7z
)

echo.
echo [3/4] 开始打包（单文件、内置完整包、无控制台窗口）...
pyinstaller --noconfirm --clean --onefile --windowed ^
    --name "DLSS5_FrameGen_Tool" ^
    --collect-all customtkinter ^
    --collect-all py7zr ^
    --add-data "OptiScaler_v0.9.4_full.7z;." ^
    DLSS5_FrameGen_Tool.py
if errorlevel 1 (
    echo [X] 打包失败
    pause
    exit /b 1
)

echo.
echo [4/4] 完成！
echo EXE 位置: dist\DLSS5_FrameGen_Tool.exe
echo （内置 OptiScaler 完整包，双击即用，无需联网）
echo.
pause
