@echo off
chcp 65001 >nul
title 🌙 曦和每日刷新

echo ╔══════════════════════════════════════╗
echo ║  曦和每日自动刷新         20:00     ║
echo ║  掘金 + 少数派 → 合并 → 部署       ║
echo ╚══════════════════════════════════════╝
echo.

set "PYTHON=C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe"

:: 确保prey目录存在
if not exist "E:\ToolPilot\prey" mkdir "E:\ToolPilot\prey"

:: 记录日志
echo [%date% %time%] 每日刷新启动 >> "E:\ToolPilot\prey\daily_refresh_log.txt"

:: 运行自动刷新脚本
"%PYTHON%" "E:\ToolPilot\sop\daily_auto.py"

:: 同步到腾讯云 COS（自动发布）
echo.
echo 📤 同步到腾讯云 COS...
"%PYTHON%" "E:\ToolPilot\deploy_cos.py" sync

if %errorlevel% equ 0 (
    echo ✅ COS 同步完成
) else (
    echo ⚠️ COS 同步失败，deploy_pending.flag 已保留
)

echo.
echo ✅ 每日刷新完成！
echo 结果已写入 data.json 并同步到腾讯云 COS
echo 下次会话时曦和会检测到部署标志并通知你
echo.
echo ═══════════════════════════════════════
pause
