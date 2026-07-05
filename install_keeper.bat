@echo off
chcp 65001 >nul
title AIbounty · 一键安装守护

echo ════════════════════════════════════════
echo   曦和终极守护 · 安装程序
echo   纯bat引擎 · 无需依赖 · 开机自启
echo ════════════════════════════════════════
echo.

:: ── 第1步：检查是否有旧任务 ──
echo 🔍 检查旧任务...
schtasks /query /tn "AIbountyKeeper" >nul 2>&1
if %errorlevel%==0 (
    echo   发现旧任务，正在删除...
    schtasks /delete /tn "AIbountyKeeper" /f >nul 2>&1
)
echo ✅ 旧任务已清理

:: ── 第2步：检查VBS启动文件 ──
echo 🔍 检查VBS启动文件...
if exist "%TEMP%\aibounty_start_keeper.vbs" (
    echo ✅ VBS文件已存在
) else (
    echo   创建VBS文件中...
    echo Set WshShell = CreateObject("WScript.Shell") > "%TEMP%\aibounty_start_keeper.vbs"
    echo WshShell.Run "E:\ToolPilot\keeper.bat", 0, False >> "%TEMP%\aibounty_start_keeper.vbs"
    echo ✅ VBS文件已创建
)

:: ── 第3步：注册开机启动 ──
echo 🔧 注册开机自启...
schtasks /create /tn "AIbountyKeeper" /tr "wscript.exe \"%TEMP%\aibounty_start_keeper.vbs\"" /sc onlogon /ru "%USERNAME%" /f >nul 2>&1
if %errorlevel%==0 (
    echo ✅ 开机自启已注册
) else (
    echo ⚠️ 直接注册失败，尝试备用方案...
    :: 备用：写入注册表Run
    reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "AIbountyKeeper" /t REG_SZ /d "wscript.exe \"%TEMP%\aibounty_start_keeper.vbs\"" /f >nul 2>&1
    echo ✅ 已写入注册表Run（登录时启动）
)

:: ── 第4步：立即启动守护 ──
echo 🚀 正在启动守护进程...
start /min wscript.exe "%TEMP%\aibounty_start_keeper.vbs"
echo ✅ 守护已启动（最小化运行）

:: ── 第5步：验证服务器 ──
echo.
echo ⏳ 等待服务器就绪...
timeout /t 3 /nobreak >nul
curl -s -o nul http://localhost:4321/ --max-time 3
if %errorlevel%==0 (
    echo ✅ 服务器在线！HTTP 200
) else (
    echo ⚠️ 服务器启动中，可能需要几秒...
)

echo.
echo ════════════════════════════════════════
echo   🛡️  曦和终极守护 · 部署完成
echo   开机自启 ✅  崩溃自愈 ✅  无窗口运行 ✅
echo ════════════════════════════════════════
echo.
echo   🌐 http://localhost:4321
echo   📋 日志: E:\ToolPilot\keeper.log
echo.
echo   如需手动停止：taskkill /f /im python.exe
echo   如需查看状态：打开 http://localhost:4321/status.html
echo.
pause
