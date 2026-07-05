@echo off
chcp 65001 >nul
title AIbounty 一键部署

set PYTHON=%~dp0..\..\Users\Administrator\.workbuddy\binaries\python\envs\default\Scripts\python.exe

echo ╔══════════════════════════════════╗
echo ║    🏴‍☠️  AIbounty 一键部署工具     ║
echo ╚══════════════════════════════════╝
echo.

if "%1"=="--help" goto help
if "%1"=="" goto deploy
if "%1"=="status" goto status
if "%1"=="sync" goto sync
if "%1"=="deploy" goto deploy
goto help

:status
echo 📋 查看存储桶状态...
%PYTHON% "%~dp0deploy_cos.py" status
goto end

:sync
echo 📤 同步文件到 COS...
%PYTHON% "%~dp0deploy_cos.py" sync
goto end

:deploy
echo 🚀 全量部署（同步+CDN刷新）...
echo.
echo   目标: https://aibounty.cn
echo   源目录: %~dp0site
echo.
choice /C YN /N /M "确认部署？(Y/N): "
if errorlevel 2 goto end
echo.
%PYTHON% "%~dp0deploy_cos.py" deploy
echo.
echo ✅ 部署完成！稍等 CDN 生效后即可访问 https://aibounty.cn
goto end

:help
echo 用法: deploy.bat [命令]
echo.
echo   无参数    全量部署到 COS + CDN 刷新
echo   status    查看存储桶状态
echo   sync      仅同步文件，不刷新 CDN
echo   deploy    全量部署
echo.
goto end

:end
echo.
pause
