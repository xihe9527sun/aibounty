@echo off
chcp 65001 >nul
title 少数派 · 曦和狩猎

echo ================================================
echo   曦和狩猎引擎 · 少数派 猎场
echo ================================================
echo.

set "PYTHON=C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe"
set "PREY=E:\ToolPilot\prey"
if not exist "%PREY%" mkdir "%PREY%"

echo 🔍 正在狩猎 AI相关内容...
echo.

:: Python代码内嵌（Base64编码）
"%PYTHON%" -c "import base64; exec(base64.b64decode('IyEvdXNyL2Jpbi9lbnYgcHl0aG9uMwoiIiLlsJHmlbDmtL7ni6nnjI7ohJrmnKwg4oCUIOiiqyBodW50X3NzcGFpLmJhdCDosIPnlKgiIiIKaW1wb3J0IHVybGxpYi5yZXF1ZXN0LCBqc29uLCBvcywgdGltZSwgc3lzCgpoZWFkZXJzID0geydVc2VyLUFnZW50JzogJ01vemlsbGEvNS4wIChXaW5kb3dzIE5UIDEwLjA7IFdpbjY0OyB4NjQpIEFwcGxlV2ViS2l0LzUzNy4zNid9ClBSRVlfRElSID0gcidFOlxUb29sUGlsb3RccHJleScKCkFJX0tXID0gWydhaScsJ2dwdCcsJ2xsbScsJ2FnZW50JywnY2hhdGdwdCcsJ2NsYXVkZScsJ+Wkp+aooeWeiycsJ+S6uuW3peaZuuiDvScsCiAgICAgICAgICdjaGF0Ym90JywncmFnJywnb3BlbmFpJywnZW1iZWRkaW5nJywn5py65Zmo5a2m5LmgJywn5rex5bqm5a2m5LmgJywKICAgICAgICAgJ25ldXJhbCcsJ3RyYW5zZm9ybWVyJywn6Ieq5Yqo5YyWJywn5pm66IO9JywndmlzaW9uJywnZ2VuZXJhdGlvbiddCgphcGlzID0gWwogICAgJ2h0dHBzOi8vc3NwYWkuY29tL2FwaS92MS9hcnRpY2xlL2hvdC9wYWdlL2dldD9saW1pdD0zMCcsCiAgICAnaHR0cHM6Ly9zc3BhaS5jb20vYXBpL3YxL2FydGljbGUvaW5kZXgvcGFnZS9nZXQ/bGltaXQ9MzAnLApdCgphcnRpY2xlcyA9IFtdCmZvciBhcGkgaW4gYXBpczoKICAgIHRyeToKICAgICAgICBwcmludChmJyAg5bCd6K+VQVBJOiB7YXBpLnNwbGl0KCI/IilbMF0uc3BsaXQoIi8iKVstMV19Li4uJykKICAgICAgICBzeXMuc3Rkb3V0LmZsdXNoKCkKICAgICAgICByZXEgPSB1cmxsaWIucmVxdWVzdC5SZXF1ZXN0KGFwaSwgaGVhZGVycz1oZWFkZXJzKQogICAgICAgIHJlc3AgPSB1cmxsaWIucmVxdWVzdC51cmxvcGVuKHJlcSwgdGltZW91dD0xNSkKICAgICAgICBkYXRhID0ganNvbi5sb2FkcyhyZXNwLnJlYWQoKSkKICAgICAgICBpdGVtcyA9IGRhdGEuZ2V0KCdkYXRhJywgW10pIGlmIGlzaW5zdGFuY2UoZGF0YSwgZGljdCkgZWxzZSAoZGF0YSBpZiBpc2luc3RhbmNlKGRhdGEsIGxpc3QpIGVsc2UgW10pCiAgICAgICAgaWYgaXRlbXM6CiAgICAgICAgICAgIGFydGljbGVzID0gaXRlbXMKICAgICAgICAgICAgcHJpbnQoZicgIOKchSDmiJDlip86IHtsZW4oaXRlbXMpfSDnr4cnKQogICAgICAgICAgICBzeXMuc3Rkb3V0LmZsdXNoKCkKICAgICAgICAgICAgYnJlYWsKICAgIGV4Y2VwdCBFeGNlcHRpb24gYXMgZToKICAgICAgICBwcmludChmJyAg4pqgIOWksei0pToge3N0cihlKVs6NDBdfScpCiAgICAgICAgc3lzLnN0ZG91dC5mbHVzaCgpCgppZiBub3QgYXJ0aWNsZXM6CiAgICBwcmludCgnICDinYwg5omA5pyJQVBJ5Z2H5aSx6LSlJykKICAgIHN5cy5leGl0KDEpCgpjb3VudCA9IDAKZm9yIGEgaW4gYXJ0aWNsZXNbOjMwXToKICAgIHRpdGxlID0gKGEuZ2V0KCd0aXRsZScsICcnKSBvciAnJykuc3RyaXAoKQogICAgaWYgbm90IHRpdGxlOiBjb250aW51ZQogICAgIyDlhbPplK7or43ov4fmu6QKICAgIHRpdGxlX2xvd2VyID0gdGl0bGUubG93ZXIoKQogICAga3dfaGl0ID0gW2t3IGZvciBrdyBpbiBBSV9LVyBpZiBrdyBpbiB0aXRsZV9sb3dlcl0KICAgIGlmIG5vdCBrd19oaXQ6IGNvbnRpbnVlCiAgICAKICAgIGFpZCA9IHN0cihhLmdldCgnaWQnLCAnJykgb3IgYS5nZXQoJ2FydGljbGVfaWQnLCAnJykgb3IgJycpCiAgICBpZiBub3QgYWlkOiBjb250aW51ZQogICAgdXJsID0gZidodHRwczovL3NzcGFpLmNvbS9wb3N0L3thaWR9JwogICAgc3VtbWFyeSA9IChhLmdldCgnc3VtbWFyeScsICcnKSBvciAnJylbOjIwMF0KICAgIAogICAgZm5hbWUgPSBmJ3RwLXNzcGFpLXtpbnQodGltZS50aW1lKCkqMTAwMCl9LXtvcy51cmFuZG9tKDIpLmhleCgpfS5qc29uJwogICAgZGF0YSA9IHsKICAgICAgICAnc291cmNlJzogJ3NzcGFpJywgJ3RpdGxlJzogdGl0bGVbOjEyMF0sICdhYnN0cmFjdCc6IHN1bW1hcnksCiAgICAgICAgJ3VybCc6IHVybCwgJ3Njb3JlJzogMCwKICAgICAgICAnY2FwdHVyZWRfYXQnOiB0aW1lLnN0cmZ0aW1lKCclWS0lbS0lZCAlSDolTTolUycpCiAgICB9CiAgICB3aXRoIG9wZW4ob3MucGF0aC5qb2luKFBSRVlfRElSLCBmbmFtZSksICd3JywgZW5jb2Rpbmc9J3V0Zi04JykgYXMgZjoKICAgICAgICBqc29uLmR1bXAoZGF0YSwgZiwgZW5zdXJlX2FzY2lpPUZhbHNlLCBpbmRlbnQ9MikKICAgIAogICAga3dfc3RyID0gJywgJy5qb2luKGt3X2hpdFs6M10pCiAgICBwcmludChmJyAg4pyFIHt0aXRsZVs6NTBdfSAgKHtrd19zdHJ9KScpCiAgICBjb3VudCArPSAxCiAgICBzeXMuc3Rkb3V0LmZsdXNoKCkKCmlmIGNvdW50ID09IDA6CiAgICBwcmludCgnXG4gIOKEue+4jyAg5pyq5Y+R546wQUnnm7jlhbPmlofnq6AnKQplbHNlOgogICAgcHJpbnQoZidcbiAg8J+OryDlhbHmjZXojrcge2NvdW50fSDmnaEnKQoKcHJpbnQoZidcbiAg57uT5p6c5bey5L+d5a2Y6IezOiB7UFJFWV9ESVJ9JykK'))"

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