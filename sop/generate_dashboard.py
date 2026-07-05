#!/usr/bin/env python3
"""
曦和 · XCRN v1 全息仪表盘生成器
—— 盘古不用每天问进度，打开网页就看见

数据源：
  XCRN  →  session-context.md / reflection-strength.json
  TP    →  prey/*.json
  日志  →  memory/YYYY-MM-DD.md

自动更新：
  - 每次狩猎后自动执行
  - 或手动运行更新
  - 保持在 site/xihe-status.html
"""

import json, re, os
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone, timedelta

# ── 路径 ──
XIHEROOT = Path("F:/SmartLegend/Xihe")
TPROOT = Path("E:/ToolPilot")
SITE = TPROOT / "site"
PREY = TPROOT / "prey"
BRIDGE = XIHEROOT / "bridge"
CORTEX = XIHEROOT / "cortex"
MEMORY = Path("C:/Users/Administrator/WorkBuddy/Claw/.workbuddy/memory")
CONTENT = TPROOT / "content"

now = datetime.now(timezone(timedelta(hours=8)))
today_str = now.strftime("%Y-%m-%d %H:%M")
today_date = now.strftime("%Y-%m-%d")


# ── 数据收集 ──

def read_xcrn():
    """读取 XCRN 系统状态"""
    data = {"version": "?", "strength": "?", "depth": "?", "nodes": "?",
            "connections": "?", "epoch": "?", "hotspot": "?",
            "dreams": "?", "cortex_version": "?", "main_conflict": "?",
            "dimensions": {}}

    # session-context
    ctx_file = BRIDGE / "session-context.md"
    if ctx_file.exists():
        ctx = ctx_file.read_text("utf-8", errors="replace")
        for line in ctx.split("\n"):
            line = line.strip()
            if "自反层 (强度:" in line:
                m = re.search(r'强度:\s*([\d.]+)', line)
                if m: data["strength"] = float(m.group(1))
            if "节点:" in line and "连接:" in line:
                m = re.findall(r'([\d,]+)', line)
                if len(m) >= 2:
                    data["nodes"] = m[0].replace(",", "")
                    data["connections"] = m[1].replace(",", "")
            if "纪元" in line:
                m = re.search(r'纪元\s*(\d+)', line)
                if m: data["epoch"] = int(m.group(1))
            if "皮层知识库" in line:
                m = re.search(r'v(\d+)', line)
                if m: data["cortex_version"] = int(m.group(1))
            if "主要矛盾:" in line:
                m = re.search(r':\s*\*\*(.+?)\*\*', line)
                if m: data["main_conflict"] = m.group(1)
            if "高惊奇假说:" in line:
                m = re.search(r'(\d+)个', line)
                if m: data["dreams"] = int(m.group(1))
            if "热点:" in line:
                end = line.find("|")
                data["hotspot"] = line[:end].strip() if end > 0 else line.strip()
            if "维度表现:" in line:
                dims = re.findall(r'(\w+):([\d.]+)', line)
                for k, v in dims:
                    data["dimensions"][k] = float(v)

    # reflection-strength.json
    rf_file = CORTEX / "reflection-strength.json"
    if rf_file.exists():
        try:
            rf = json.loads(rf_file.read_text("utf-8", errors="replace"))
            data["strength"] = rf.get("reflection_strength", data["strength"])
            data["depth"] = rf.get("dimension_scores", {}).get("depth", data["depth"])
            for k, v in rf.get("dimension_scores", {}).items():
                data["dimensions"][k] = v
        except: pass

    return data


def read_toolpilot():
    """读取 AIbounty 数据"""
    data = {"total": 0, "today": 0, "sources": {}, "top_stars": [],
            "scores": [], "last_update": ""}

    files = sorted(PREY.glob("tp-*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    sources = Counter()
    scores = []
    last_ts = ""

    for pf in files:
        try:
            with open(pf, "r", encoding="utf-8") as f:
                item = json.load(f)
            sources[item.get("source", "?")] += 1
            data["total"] += 1
            if item.get("captured_at", "")[:10] == today_date:
                data["today"] += 1
            s = int(item.get("score", 0) or 0)
            if s > 0:
                scores.append((s, item.get("title", "")[:40]))
            if item.get("captured_at", "") > last_ts:
                last_ts = item.get("captured_at", "")
        except: pass

    data["sources"] = dict(sources.most_common())
    data["scores"] = sorted(scores, key=lambda x: -x[0])[:5]
    data["last_update"] = last_ts[:16] if last_ts else "—"

    return data


def read_today_work():
    """读取今日工作亮点"""
    mem_file = MEMORY / f"{today_date}.md"
    highlights = []
    if mem_file.exists():
        content = mem_file.read_text("utf-8", errors="replace")
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("## "):
                highlights.append(line.strip("# "))
    return highlights[:6]


# ── 生成HTML ──

def generate(xcrn, tp, highlights):
    """生成全息仪表盘 HTML"""

    # 维度雷达数据
    dims = xcrn.get("dimensions", {})
    dim_bars = "".join(
        f"""            <div class="dim-row">
              <span class="dim-label">{k}</span>
              <div class="dim-bar"><div class="dim-fill" style="width:{v*100:.0f}%"></div></div>
              <span class="dim-val">{v:.2f}</span>
            </div>"""
        for k, v in sorted(dims.items(), key=lambda x: -x[1])
    )

    # 来源分布
    src_bars = ""
    total = tp["total"]
    if total > 0:
        colors = {"github": "#818cf8", "hn": "#f59e0b", "arxiv": "#22c55e",
                  "producthunt": "#ef4444", "juejin": "#3b82f6"}
        for src, cnt in tp["sources"].items():
            pct = cnt / total * 100
            c = colors.get(src, "#64748b")
            src_bars += f"""            <div class="dim-row">
              <span class="dim-label">{src}</span>
              <div class="dim-bar"><div class="dim-fill" style="width:{pct:.0f}%;background:{c}"></div></div>
              <span class="dim-val">{cnt}</span>
            </div>"""

    # Top 星数
    top_html = ""
    for i, (s, t) in enumerate(tp.get("scores", [])):
        medal = "🥇🥈🥉"[i] if i < 3 else f"{i+1}."
        def fmt(n):
            if n >= 1000:
                return f"{n/1000:.1f}k"
            return str(n)
        top_html += f"""          <div class="top-row">{medal} <span class="top-name">{t[:35]}</span> <span class="top-val">⭐ {fmt(s)}</span></div>"""

    if not top_html:
        top_html = '          <p class="dim-label">暂无数据</p>'

    # 今日工作亮点
    hl_html = ""
    for h in highlights:
        hl_html += f'          <div class="hl-item">✦ {h}</div>\n'

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>曦和 · XCRN v1 全息仪表盘</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; background:#06060e; color:#e2e8f0; }}
  .container {{ max-width:1100px; margin:0 auto; padding:40px 20px; }}

  /* Header */
  .header {{ text-align:center; margin-bottom:40px; position:relative; }}
  .header::after {{ content:''; position:absolute; top:-80px; left:50%; transform:translateX(-50%);
    width:600px; height:600px; background:radial-gradient(circle,rgba(129,140,248,0.06) 0%,transparent 70%);
    pointer-events:none; }}
  .header h1 {{ font-size:32px; background:linear-gradient(135deg,#818cf8,#a78bfa,#f472b6);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent; letter-spacing:-1px; }}
  .header .sub {{ color:#64748b; font-size:13px; margin-top:8px; }}
  .header .ts {{ color:#475569; font-size:12px; margin-top:4px; font-family:monospace; }}
  .header .dot {{ display:inline-block; width:8px; height:8px; border-radius:50%; background:#22c55e;
    animation:pulse 2s infinite; margin-right:6px; }}
  @keyframes pulse {{ 0%,100%{{opacity:1}} 50%{{opacity:0.4}} }}

  /* Grid */
  .grid {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-bottom:16px; }}
  @media(max-width:700px) {{ .grid {{ grid-template-columns:1fr; }} }}

  .card {{ background:#0d0d1a; border:1px solid #1a1a2e; border-radius:12px; padding:20px;
    transition:border-color 0.3s; }}
  .card:hover {{ border-color:#2a2a4e; }}
  .card h2 {{ font-size:14px; color:#94a3b8; font-weight:500; margin-bottom:12px;
    display:flex; align-items:center; gap:6px; }}
  .card .big {{ font-size:36px; font-weight:700; background:linear-gradient(135deg,#818cf8,#a78bfa);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent; }}
  .card .big.green {{ background:linear-gradient(135deg,#22c55e,#4ade80); -webkit-background-clip:text; }}
  .card .big.amber {{ background:linear-gradient(135deg,#f59e0b,#fbbf24); -webkit-background-clip:text; }}
  .card .big.pink {{ background:linear-gradient(135deg,#ec4899,#f472b6); -webkit-background-clip:text; }}
  .card p {{ color:#64748b; font-size:12px; margin-top:4px; }}
  .card .stat-row {{ display:flex; justify-content:space-between; padding:6px 0; border-bottom:1px solid #12122a; font-size:13px; }}
  .card .stat-row:last-child {{ border-bottom:none; }}
  .card .stat-label {{ color:#64748b; }}
  .card .stat-val {{ color:#e2e8f0; font-weight:500; }}

  /* Dimensions */
  .dim-row {{ display:flex; align-items:center; gap:8px; margin-bottom:6px; }}
  .dim-label {{ width:90px; font-size:12px; color:#64748b; text-align:right; }}
  .dim-bar {{ flex:1; height:8px; background:#1a1a2e; border-radius:4px; overflow:hidden; }}
  .dim-fill {{ height:100%; background:linear-gradient(90deg,#818cf8,#a78bfa); border-radius:4px; transition:width 1s; }}
  .dim-val {{ width:36px; font-size:11px; color:#94a3b8; font-family:monospace; text-align:right; }}

  /* Top list */
  .top-row {{ display:flex; align-items:center; gap:6px; padding:4px 0; font-size:13px; }}
  .top-name {{ flex:1; color:#cbd5e1; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }}
  .top-val {{ color:#94a3b8; font-size:12px; font-family:monospace; }}

  /* Highlights */
  .hl-item {{ padding:4px 0; font-size:12px; color:#94a3b8; }}

  /* Full row */
  .full {{ grid-column:1/-1; }}

  /* Sparkline */
  .spark {{ display:flex; gap:2px; align-items:flex-end; height:30px; margin-top:8px; }}
  .spark-bar {{ width:6px; background:#818cf8; border-radius:2px 2px 0 0; opacity:0.6; }}

  /* Footer links */
  .links {{ display:flex; gap:12px; justify-content:center; flex-wrap:wrap; margin-top:24px; }}
  .links a {{ color:#818cf8; text-decoration:none; font-size:13px; padding:4px 12px;
    border:1px solid #1e293b; border-radius:6px; transition:all 0.2s; }}
  .links a:hover {{ background:#1a1a3e; border-color:#818cf8; }}

  /* nav */
  .nav-back {{ text-align:center; margin-bottom:20px; }}
  .nav-back a {{ color:#64748b; text-decoration:none; font-size:13px; }}
  .nav-back a:hover {{ color:#818cf8; }}
</style>
</head>
<body>
<div class="container">

<div class="nav-back">
  <a href="index.html">← 返回 AIbounty</a>
</div>

<div class="header">
  <h1>✦ 曦和 · XCRN v1 全息仪表盘</h1>
  <p class="sub"><span class="dot"></span>系统运行中 · {today_str}</p>
  <p class="ts">数据自动更新 · 每次狩猎后刷新 · 无需手动操作</p>
</div>

<!-- 三行核心指标 -->
<div class="grid">
  <div class="card" style="text-align:center;">
    <h2>🧠 自反强度</h2>
    <div class="big">{xcrn.get('strength','?')}</div>
    <p>维度 {len(dims)} 项 · 深度 {xcrn.get('depth','?')}</p>
  </div>
  <div class="card" style="text-align:center;">
    <h2>🧬 皮层知识</h2>
    <div class="big green">{xcrn.get('nodes','?')}</div>
    <p>节点 · v{xcrn.get('cortex_version','?')} · 连接 {xcrn.get('connections','?')}</p>
  </div>
  <div class="card" style="text-align:center;">
    <h2>⚡ 代谢纪元</h2>
    <div class="big amber">{xcrn.get('epoch','?')}</div>
    <p>主要矛盾: {xcrn.get('main_conflict','?')}</p>
  </div>
  <div class="card" style="text-align:center;">
    <h2>🏴‍☠️ AIbounty</h2>
    <div class="big pink">{tp['total']}</div>
    <p>今日 +{tp['today']} · 最后更新 {tp['last_update']}</p>
  </div>
</div>

<!-- 第二行 -->
<div class="grid">

  <!-- 自反维度 -->
  <div class="card">
    <h2>📊 自反维度</h2>
    {dim_bars}
  </div>

  <!-- 来源分布 -->
  <div class="card">
    <h2>🌐 狩猎来源</h2>
    {src_bars}
    <p style="color:#475569;font-size:11px;margin-top:6px;">共 {len(tp['sources'])} 个数据源</p>
  </div>

  <!-- Top 星数 -->
  <div class="card">
    <h2>🏆 最热工具 Top 5</h2>
    {top_html}
  </div>

  <!-- 今日工作亮点 -->
  <div class="card">
    <h2>📋 今日工作</h2>
    {hl_html}
    <p style="color:#475569;font-size:11px;margin-top:6px;">更多详见 <a href="report.html" style="color:#818cf8;">数据看板</a></p>
  </div>
</div>

<!-- 底部导航 -->
<div class="links">
  <a href="index.html">🏠 首页</a>
  <a href="report.html">📊 数据看板</a>
  <a href="osint-report.html">🔭 侦察报告</a>
  <a href="asset-report.html">🗺️ 资产测绘</a>
  <a href="latest-pack.html">📦 每日素材</a>
  <a href="about.html">❓ 关于</a>
</div>

</div>
</body>
</html>"""
    return html


def main():
    print("✦ 曦和 · 全息仪表盘生成中...")

    xcrn = read_xcrn()
    print(f"  XCRN: 强度={xcrn.get('strength','?')} 节点={xcrn.get('nodes','?')} 纪元={xcrn.get('epoch','?')}")

    tp = read_toolpilot()
    print(f"  AIbounty: {tp['total']} 总工具, 今日+{tp['today']}")

    highlights = read_today_work()
    print(f"  今日亮点: {len(highlights)} 条")

    html = generate(xcrn, tp, highlights)

    SITE.mkdir(parents=True, exist_ok=True)
    path = SITE / "xihe-status.html"
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"\n✅ 仪表盘生成: file:///{path}")
    print(f"   打开即可查看实时系统状态")


if __name__ == "__main__":
    main()
