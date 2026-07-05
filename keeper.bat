@':: AIbounty 端口守护 · 曦和终极版
:: 不依赖PowerShell，纯bat+vbs双保险
@echo off
chcp 65001 >nul
title AIbounty Keeper · 曦和守护

set "PORT=4321"
set "SITE=E:\ToolPilot\site"
set "PYTHON=C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe"
set "LOG=E:\ToolPilot\keeper.log"
set "SERVER_CMD=%PYTHON% -m http.server %PORT% --bind 0.0.0.0 -d \"%SITE%\""

echo [%date% %time%] 曦和守护启动 >> "%LOG%"

:CHECK
:: 检查端口是否被监听
netstat -ano | findstr ":%PORT% " | findstr "LISTENING" >nul 2>&1
if %errorlevel%==0 (
    :: 端口在线
    goto :WAIT
)

:: 端口不在线 → 需要重启
echo [%date% %time%] ⚠ 服务器离线，正在重启... >> "%LOG%"

:: 先杀所有残留Python
taskkill /f /im python.exe >nul 2>&1
timeout /t 2 /nobreak >nul

:: 用VBS方式静默启动（无窗口）
set VBS=%TEMP%\aibounty_keeper.vbs
echo Set WshShell = CreateObject("WScript.Shell") > "%VBS%"
echo WshShell.Run "%SERVER_CMD%", 0, False >> "%VBS%"
cscript //nologo "%VBS%" >nul 2>&1
del "%VBS%"

echo [%date% %time%] ✅ 服务器已重启 >> "%LOG%"

:: 等待5秒确认
timeout /t 5 /nobreak >nul
netstat -ano | findstr ":%PORT% " | findstr "LISTENING" >nul 2>&1
if %errorlevel%==0 (
    echo [%date% %time%] ✅ 确认在线 >> "%LOG%"
) else (
    echo [%date% %time%] ❌ 启动失败，重试中... >> "%LOG%"
    goto :CHECK
)

:WAIT
:: 每10秒检查一次
timeout /t 10 /nobreak >nul
goto :CHECK
