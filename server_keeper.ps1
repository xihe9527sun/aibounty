# AIbounty Server Keeper — 曦和端口守护 v2.0
# 开机自启，崩溃自愈，无需人工干预

$port = 4321
$siteDir = "E:\ToolPilot\site"
$python = "C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe"
$logFile = "E:\ToolPilot\server_keeper.log"
$serverProcess = $null

function Log {
    param($msg)
    $time = Get-Date -Format "HH:mm:ss"
    "$time | $msg" | Out-File -FilePath $logFile -Append -Encoding UTF8
}

function Start-Server {
    Log "启动服务器..."
    # 杀旧进程
    netstat -ano | findstr ":$port " | findstr "LISTENING" | ForEach-Object {
        $p = $_ -replace '.*\s+(\d+)\s*$', '$1'
        if ($p -match '^\d+$') { taskkill /f /pid $p 2>$null }
    }
    Start-Sleep 1
    # 启动新服务器
    $script:serverProcess = Start-Process -FilePath $python -ArgumentList "-m http.server $port --bind 0.0.0.0 -d `"$siteDir`"" -WindowStyle Hidden -PassThru
    Log "服务器已启动 (PID: $($serverProcess.Id))"
}

function Test-Server {
    try {
        $req = [System.Net.HttpWebRequest]::Create("http://localhost:$port/")
        $req.Timeout = 3000
        $resp = $req.GetResponse()
        $resp.Close()
        return $true
    } catch {
        return $false
    }
}

# 主循环
Log "═══════════ 守护启动 ═══════════"
Log "端口: $port | 目录: $siteDir"

Start-Server

while ($true) {
    $alive = Test-Server
    if (-not $alive) {
        Log "服务器无响应！正在检查进程..."
        $procAlive = $false
        if ($serverProcess -and !$serverProcess.HasExited) { $procAlive = $true }
        if (-not $procAlive) {
            Log "进程已死，重启中..."
            Start-Server
        }
    }
    Start-Sleep -Seconds 15
}
