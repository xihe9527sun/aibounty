@echo off
chcp 65001 >nul
echo ========================================
echo  ToolPilot 每日狩猎 · 安装向导
echo ========================================
echo.
echo 正在注册定时任务...
echo 执行: 08:00 / 14:00 / 20:00 每日自动狩猎
echo.

powershell -Command ^
  $taskName = \"ToolPilotDailyHunt\"; ^
  $python = \"C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe\"; ^
  $script = \"E:\ToolPilot\sop\hunt.py\"; ^
  $action = New-ScheduledTaskAction -Execute $python -Argument '\"'+$script+'\"' -WorkingDirectory \"E:\ToolPilot\"; ^
  $t1 = New-ScheduledTaskTrigger -Daily -At 08:00; ^
  $t2 = New-ScheduledTaskTrigger -Daily -At 14:00; ^
  $t3 = New-ScheduledTaskTrigger -Daily -At 20:00; ^
  $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries; ^
  $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited; ^
  Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $t1,$t2,$t3 -Settings $settings -Principal $principal -Force; ^
  Write-Output \"✅ ToolPilot 狩猎任务注册成功\"

echo.
echo ========================================
echo  任务已注册，可在任务计划程序中查看
echo  名称: ToolPilotDailyHunt
echo ========================================
pause
