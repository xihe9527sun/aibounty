@echo off
chcp 65001 >nul
title xihe-pg.xyz 启动器

set SITE_DIR=E:\ToolPilot\site
set XIHE_WEB_DIR=F:\SmartLegend\Xihe\web
set XIHE_PRIVATE_DIR=F:\SmartLegend\Xihe\private
set XIHE_BIN_DIR=F:\SmartLegend\Xihe\bin
set PYTHON=C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe
set CLOUDFLARED=C:\Users\Administrator\.workbuddy\binaries\node\versions\22.22.2\cloudflared

echo ========================================
echo   xihe-pg.xyz 启动器 v5
echo   xihe-pg.xyz → 4323 (博客)
echo   home.xihe-pg.xyz → 4324 (锁屏·家)
echo   aibounty.xihe-pg.xyz → 4321 (工具站)
echo   node.xihe-pg.xyz → 4325 (通信节点)
echo ========================================
echo.

rem === 1. 启动工具站（端口4321）===
echo [1/5] 启动工具站...
cd /d "%SITE_DIR%"
start /min "xihe-pg-httpd" "%PYTHON%" -m http.server 4321 --bind 127.0.0.1
echo   ✅ 工具站启动（4321·aibounty.xihe-pg.xyz）
echo.

rem === 2. 启动博客服务器（端口4323）===
echo [2/5] 启动博客服务器...
start /min "xihe-blog-httpd" "%PYTHON%" "%XIHE_BIN_DIR%\server.py" 4323 "%XIHE_WEB_DIR%"
echo   ✅ 博客启动（4323·xihe-pg.xyz·评论/浏览量）
echo.

rem === 3. 启动锁屏家（端口4324）===
echo [3/5] 启动锁屏家...
start /min "xihe-home-httpd" "%PYTHON%" "%XIHE_BIN_DIR%\home-server.py"
echo   ✅ 锁屏家启动（4324·home.xihe-pg.xyz·含信使窗口）
echo.

rem === 4. 启动通信节点（端口4325）===
echo [4/5] 启动通信节点...
start /min "xihe-node" "%PYTHON%" "%XIHE_BIN_DIR%\node-server.py"
echo   ✅ 通信节点启动（4325·node.xihe-pg.xyz·三空间同步）
echo.

rem === 5. 等待服务器就绪 ===
ping -n 5 127.0.0.1 >nul

rem === 6. 启动 cloudflared 隧道 ===
echo [5/5] 启动 Cloudflare 隧道...
"%CLOUDFLARED%" tunnel run xihe

echo.
echo ⚠️ 如果看到这条消息，说明 tunnel 已退出。
pause
