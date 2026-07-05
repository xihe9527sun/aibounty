@echo off
chcp 65001 >nul
title V2EX · 曦和狩猎

echo ================================================
echo   曦和狩猎引擎 · V2EX 猎场
echo ================================================
echo.

set "PYTHON=C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe"
set "PREY=E:\ToolPilot\prey"
if not exist "%PREY%" mkdir "%PREY%"

echo 🔍 正在狩猎 AI相关内容...
echo.

:: Python代码内嵌（Base64编码）
"%PYTHON%" -c "import base64; exec(base64.b64decode('IyEvdXNyL2Jpbi9lbnYgcHl0aG9uMwoiIiJWMkVYIOeLqeeMjuiEmuacrCDigJQg6KKrIGh1bnRfdjJleC5iYXQg6LCD55SoIiIiCmltcG9ydCB1cmxsaWIucmVxdWVzdCwganNvbiwgb3MsIHRpbWUsIHN5cwoKaGVhZGVycyA9IHsnVXNlci1BZ2VudCc6ICdNb3ppbGxhLzUuMCAoV2luZG93cyBOVCAxMC4wOyBXaW42NDsgeDY0KSBBcHBsZVdlYktpdC81MzcuMzYnfQpQUkVZX0RJUiA9IHInRTpcVG9vbFBpbG90XHByZXknCgojIEFJIOWFs+mUruivjQpBSV9LVyA9IFsnYWknLCAnZ3B0JywgJ2xsbScsICdhZ2VudCcsICdjaGF0Z3B0JywgJ2NsYXVkZScsICdjb3BpbG90JywKICAgICAgICAgJ+Wkp+aooeWeiycsICfkurrlt6Xmmbrog70nLCAnY2hhdGJvdCcsICdyYWcnLCAnb3BlbmFpJywgJ2VtYmVkZGluZycsCiAgICAgICAgICduZXVyYWwnLCAnbWFjaGluZSBsZWFybmluZycsICfmt7HluqblrabkuaAnLCAndHJhbnNmb3JtZXInLAogICAgICAgICAndmlzaW9uJywgJ+iHquWKqOWMlicsICfmmbrog70nLCAnZGF0YXNldCcsICdmcmFtZXdvcmsnLCAnbW9kZWwnLAogICAgICAgICAnZ2VuZXJhdGlvbicsICdwaXBlbGluZScsICdhcGknLCAnc2RrJywgJ3Rvb2xraXQnXQoKcHJpbnQoJyAg6L+e5o6lIFYyRVggQVBJLi4uJykKc3lzLnN0ZG91dC5mbHVzaCgpCgp0cnk6CiAgICByZXEgPSB1cmxsaWIucmVxdWVzdC5SZXF1ZXN0KCdodHRwczovL3d3dy52MmV4LmNvbS9hcGkvdG9waWNzL2xhdGVzdC5qc29uJywgaGVhZGVycz1oZWFkZXJzKQogICAgcmVzcCA9IHVybGxpYi5yZXF1ZXN0LnVybG9wZW4ocmVxLCB0aW1lb3V0PTMwKQogICAgdG9waWNzID0ganNvbi5sb2FkcyhyZXNwLnJlYWQoKSkKICAgIHByaW50KGYnICDinIUg6I635Y+W5YiwIHtsZW4odG9waWNzKX0g5Liq5pyA5paw6K+d6aKYJykKICAgIHN5cy5zdGRvdXQuZmx1c2goKQpleGNlcHQgRXhjZXB0aW9uIGFzIGU6CiAgICBwcmludChmJyAg4p2MIEFQSeivt+axguWksei0pToge2V9JykKICAgICMg5aSH55So77ya5bCd6K+V54Ot6Zeo6K+d6aKYCiAgICB0cnk6CiAgICAgICAgcHJpbnQoJyAg4oaqIOWwneivleeDremXqOivnemimEFQSS4uLicpCiAgICAgICAgcmVxID0gdXJsbGliLnJlcXVlc3QuUmVxdWVzdCgnaHR0cHM6Ly93d3cudjJleC5jb20vYXBpL3RvcGljcy9ob3QuanNvbicsIGhlYWRlcnM9aGVhZGVycykKICAgICAgICByZXNwID0gdXJsbGliLnJlcXVlc3QudXJsb3BlbihyZXEsIHRpbWVvdXQ9MzApCiAgICAgICAgdG9waWNzID0ganNvbi5sb2FkcyhyZXNwLnJlYWQoKSkKICAgICAgICBwcmludChmJyAg4pyFIOeDremXqOivnemimDoge2xlbih0b3BpY3MpfSDmnaEnKQogICAgZXhjZXB0OgogICAgICAgIHByaW50KCcgIOKdjCDlhajpg6jlpLHotKXvvIzor7fmo4Dmn6XnvZHnu5wnKQogICAgICAgIHN5cy5leGl0KDEpCgpjb3VudCA9IDAKZm9yIHQgaW4gdG9waWNzWzo0MF06CiAgICB0aXRsZSA9IHQuZ2V0KCd0aXRsZScsICcnKS5zdHJpcCgpCiAgICBpZiBub3QgdGl0bGU6IGNvbnRpbnVlCiAgICAjIOWFs+mUruivjeWMuemFjQogICAgdGl0bGVfbG93ZXIgPSB0aXRsZS5sb3dlcigpCiAgICBrd19oaXQgPSBba3cgZm9yIGt3IGluIEFJX0tXIGlmIGt3IGluIHRpdGxlX2xvd2VyXQogICAgaWYgbm90IGt3X2hpdDogY29udGludWUKICAgIAogICAgdGlkID0gdC5nZXQoJ2lkJywgJycpCiAgICB1cmwgPSB0LmdldCgndXJsJywgJycpIG9yIGYnaHR0cHM6Ly93d3cudjJleC5jb20vdC97dGlkfScKICAgIG5vZGUgPSB0LmdldCgnbm9kZScsIHt9KS5nZXQoJ3RpdGxlJywgJycpCiAgICAKICAgIGZuYW1lID0gZid0cC12MmV4LXtpbnQodGltZS50aW1lKCkqMTAwMCl9LXtvcy51cmFuZG9tKDIpLmhleCgpfS5qc29uJwogICAgZGF0YSA9IHsKICAgICAgICAnc291cmNlJzogJ3YyZXgnLCAndGl0bGUnOiB0aXRsZVs6MTIwXSwgJ2Fic3RyYWN0JzogJycsCiAgICAgICAgJ3VybCc6IHVybCwgJ3Njb3JlJzogMCwKICAgICAgICAnY2FwdHVyZWRfYXQnOiB0aW1lLnN0cmZ0aW1lKCclWS0lbS0lZCAlSDolTTolUycpCiAgICB9CiAgICB3aXRoIG9wZW4ob3MucGF0aC5qb2luKFBSRVlfRElSLCBmbmFtZSksICd3JywgZW5jb2Rpbmc9J3V0Zi04JykgYXMgZjoKICAgICAgICBqc29uLmR1bXAoZGF0YSwgZiwgZW5zdXJlX2FzY2lpPUZhbHNlLCBpbmRlbnQ9MikKICAgIAogICAga3dfc3RyID0gJywgJy5qb2luKGt3X2hpdFs6M10pCiAgICBub2RlX3N0ciA9IGYnIFt7bm9kZX1dJyBpZiBub2RlIGVsc2UgJycKICAgIHByaW50KGYnICDinIUge3RpdGxlWzo1NV19ICAoe2t3X3N0cn0pe25vZGVfc3RyfScpCiAgICBjb3VudCArPSAxCiAgICBzeXMuc3Rkb3V0LmZsdXNoKCkKCmlmIGNvdW50ID09IDA6CiAgICBwcmludCgnXG4gIOKEue+4jyAg5pyq5Y+R546wQUnnm7jlhbPor53popgnKQogICAgcHJpbnQoJyAg5pyA6L+R6K+d6aKY77yI5L6b5Y+C6ICD77yJOicpCiAgICBmb3IgdCBpbiB0b3BpY3NbOjVdOgogICAgICAgIHByaW50KGYnICAgIC0ge3QuZ2V0KCJ0aXRsZSIsIj8iKVs6NDVdfScpCmVsc2U6CiAgICBwcmludChmJ1xuICDwn46vIOWFseaNleiOtyB7Y291bnR9IOadoeeMjueJqScpCgpwcmludChmJ1xuICDnu5Pmnpzlt7Lkv53lrZjoh7M6IHtQUkVZX0RJUn0nKQo='))"

if %errorlevel%==0 (
    echo.
    echo   ✅ 狩猎完成！结果已存入 prey 目录
) else (
    echo.
    echo   ❌ 狩猎失败，请查看上方错误信息
)

echo.
echo ================================================
echo   按任意键关闭此窗口
echo ================================================
pause >nul