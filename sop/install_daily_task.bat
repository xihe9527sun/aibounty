@echo off
chcp 65001 >nul
title ⚙️ 安装每日自动刷新计划任务

echo ╔══════════════════════════════════════╗
echo ║  安装每日自动刷新计划任务           ║
echo ║  每天 20:00 自动运行                ║
echo ╚══════════════════════════════════════╝
echo.

set "TASK_NAME=XiheDailyRefresh"
set "SCRIPT_PATH=E:\ToolPilot\sop\daily_refresh.bat"

:: 检查是否有管理员权限
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  需要管理员权限！
    echo    请右键此文件 → 以管理员身份运行
    pause
    exit /b 1
)

:: 删除旧任务（如果存在）
schtasks /delete /tn "%TASK_NAME%" /f >nul 2>&1

:: 创建新任务
schtasks /create ^
    /tn "%TASK_NAME%" ^
    /tr "\"%SCRIPT_PATH%\"" ^
    /sc daily ^
    /st 20:00 ^
    /f ^
    /ru %USERNAME% ^
    /rl highest

if %errorlevel% equ 0 (
    echo.
    echo ✅ 计划任务安装成功！
    echo   任务名: %TASK_NAME%
    echo   运行时间: 每天 20:00
    echo   脚本路径: %SCRIPT_PATH%
    echo.
    echo 📋 可以随时在"任务计划程序"中查看和管理
    echo   或运行以下命令手动测试:
    echo   schtasks /run /tn "%TASK_NAME%"
) else (
    echo.
    echo ❌ 安装失败，请检查权限
)

echo.
echo ═══════════════════════════════════════
pause
