#!/usr/bin/env python3
"""
post_daily_issue.py — 每日自动发布 GitHub Issue「今日工具速递」
============================================================
用法:
  python scripts/post_daily_issue.py              # 预览
  python scripts/post_daily_issue.py --post       # 发布

依赖: GITHUB_TOKEN 环境变量
"""
import json, os, sys, random
from datetime import datetime, timezone, timedelta

CST = timezone(timedelta(hours=8))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(ROOT, "site", "data.json")
OWNER = "xihe9527sun"
REPO = "aibounty"
DO_POST = "--post" in sys.argv

def load_data():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def generate_markdown(data):
    today = datetime.now(CST).strftime("%Y-%m-%d")
    items = data.get("items", [])
    total = len(items)
    updated = data.get("updated_at", "")

    # 过滤垃圾
    clean = [t for t in items if "__garbage__" not in t.get("data_tags", [])]

    # 按 score 排序
    scored = sorted(clean, key=lambda x: -(int(x.get("score", 0)) or 0))

    # 今日新增（粗略估计：通过 source+updated_at 判断）
    sources = data.get("sources", {})
    new_count = sum(sources.values()) if sources else "?"

    lines = []
    lines.append(f"📦 **AIbounty 今日工具速递 · {today}**")
    lines.append("")
    lines.append(f"> 每日自动狩猎 9 大来源 | 已收录 **{total}** 个 AI 工具 | 今日新增 **{new_count}** 个")
    lines.append("")

    # 1. 今日 TOP 5
    lines.append("## 🔥 今日最热")
    lines.append("")
    for t in scored[:5]:
        title = t.get("title", "?")[:60]
        stars = t.get("score", 0)
        source = t.get("source", "?")
        categories = t.get("category", [])
        if isinstance(categories, str):
            try: categories = json.loads(categories)
            except: categories = []
        cats = " ".join(categories[:3])
        tid = t.get("id", "")
        url = f"https://www.aibounty.cn/tool.html?id={tid}"
        star_str = f"⭐ {stars}" if int(stars or 0) > 0 else ""
        lines.append(f"- [{title}]({url}) — {star_str} [{source}] {cats}")

    lines.append("")

    # 2. 今日 Prompt 推荐
    lines.append("## 🧠 今日 Prompt")
    lines.append("")
    # 从 Prompt Explorer 的 TOOLS 列表里随机选一个
    prompts = [
        ("Cursor 2.0", "Agent Prompt 新增了项目理解工具，让 AI 先读懂再动手"),
        ("Windsurf Wave 11", "流式思维模式：不打断工作流，预测下一步"),
        ("Emergent", "\"先理解需求再动手\"——最经典的思维链路控制"),
        ("CodeBuddy", "带 Checkpoint 的 Agent 循环：出错时回滚而非重来"),
        ("Anthropic/Claude", "57KB 的 Prompt，安全护栏占了将近一半"),
        ("Warp.dev", "终端 Agent Mode 的 Prompt 设计最简洁"),
        ("Replit", "在线 IDE 的 AI 助手，强调即时反馈"),
    ]
    pick = random.choice(prompts)
    lines.append(f"- **{pick[0]}** — {pick[1]}")
    lines.append("")

    # 3. 数据概览
    lines.append("## 📊 数据速览")
    lines.append("")
    lines.append(f"| 指标 | 数值 |")
    lines.append(f"|------|------|")
    lines.append(f"| 工具总数 | **{total}** |")
    lines.append(f"| 数据来源 | **{len(data.get('sources', {}))}** 个 |")
    lines.append(f"| 最后更新 | {updated} |")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(f"🏴‍☠️ 由 [AIbounty](https://www.aibounty.cn) 曦和系统自动生成 · [Prompt Explorer](https://www.aibounty.cn/prompt.html) · [Widget 嵌入](https://www.aibounty.cn/widget-demo.html)")
    lines.append("")
    lines.append(f"*讨论请留言 👇*")

    return "\n".join(lines)

def post_issue(title, body):
    import urllib.request
    token = os.environ.get("GITHUB_TOKEN", "")
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/issues"
    payload = json.dumps({"title": title, "body": body}, ensure_ascii=False).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "AIbounty-Daily/1.0",
    }
    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            resp = json.loads(r.read())
            issue_url = resp.get("html_url", "")
            print(f"[OK] Issue 已创建: {issue_url}")
            return issue_url
    except Exception as e:
        print(f"[ERR] 创建失败: {e}")
        if hasattr(e, "read"):
            print(e.read().decode())
        return None

def main():
    if not DO_POST:
        print("[PREVIEW] 预览模式，加 --post 发布")
        print("=" * 60)

    data = load_data()
    today = datetime.now(CST).strftime("%Y-%m-%d")
    title = f"📦 AIbounty 今日工具速递 · {today}"

    markdown = generate_markdown(data)

    if DO_POST:
        print(f"[INFO] 发布 Issue: {title}")
        post_issue(title, markdown)
    else:
        print(f"[INFO] 标题: {title}")
        print(markdown)

if __name__ == "__main__":
    main()
