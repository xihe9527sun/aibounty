@echo off
chcp 65001 >nul
title AIbounty · 紧急杀进程

echo ════════════════════════════════════════
echo   AIbounty 一键杀进程 + 重启
echo   曦和容灾脚本
echo ════════════════════════════════════════

echo.
echo 🔪 正在查找所有占用 4321 端口的进程...
echo.

set "COUNT=0"
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":4321 " ^| findstr "LISTENING"') do (
    echo   结束进程 PID: %%a
    taskkill /f /pid %%a >nul 2>&1
    set /a COUNT+=1
)

if %COUNT%==0 (
    echo ✅ 没有发现占用 4321 的进程
) else (
    echo ✅ 已清理 %COUNT% 个进程
)

echo.
echo 按任意键启动服务器，或关闭窗口退出...
pause >nul

start "AIbounty Server" "E:\ToolPilot\start_aibounty_server.bat"
