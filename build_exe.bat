@echo off
chcp 65001 >nul
title DLSS 5 Frame Gen Tool - Build EXE
echo ============================================
echo   DLSS 5 + 帧生成工具 - 一键打包 EXE
echo ============================================
echo.
python --version >nul 2>&1
if errorlevel 1 (
    echo [X] 未检测到 Python，请先安装 Python 3.10+ 并勾选 Add to PATH
    pause
    exit /b 1
)
echo [1/3] 安装依赖...
python -m pip install --upgrade pip
python -m pip install customtkinter pillow pyinstaller
if errorlevel 1 (
    echo [X] 依赖安装失败
    pause
    exit /b 1
)
echo.
echo [2/3] 开始打包（单文件、无控制台窗口）...
pyinstaller --noconfirm --clean --onefile --windowed ^
    --name "DLSS5_FrameGen_Tool" ^
    --collect-all customtkinter ^
    DLSS5_FrameGen_Tool.py
if errorlevel 1 (
    echo [X] 打包失败
    pause
    exit /b 1
)
echo.
echo [3/3] 完成！
echo EXE 位置: dist\DLSS5_FrameGen_Tool.exe
echo.
pause
