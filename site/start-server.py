#!/usr/bin/env python3
"""启动AIbounty网站服务器"""
import os, subprocess, sys

SITE_DIR = "E:/ToolPilot/site"
PID_FILE = os.path.join(SITE_DIR, ".server.pid")

os.chdir(SITE_DIR)

# 启动新的
proc = subprocess.Popen(
    [sys.executable, "-m", "http.server", "4321", "--bind", "127.0.0.1"],
    cwd=SITE_DIR,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)

with open(PID_FILE, "w") as f:
    f.write(str(proc.pid))

print(f"AIbounty server started on port 4321 (PID: {proc.pid})")
print(f"Serving: {SITE_DIR}")
