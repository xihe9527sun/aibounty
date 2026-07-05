#!/usr/bin/env python3
"""
generate-daily.py — aibounty每日日报自动生成
===============================
读取 data.json → 筛选今日推荐/精选/趋势 → 生成盘古风格日报 → 输出 HTML

使用：
  python generate-daily.py              # 今天
  python generate-daily.py --date 2026-06-26  # 指定日期

风格：短句、直接、接地气、不废话、幽默诙谐、有态度
"""

import json, os, sys
from datetime import datetime, timezone, timedelta

CST = timezone(timedelta(hours=8))
DATA_FILE = os.path.join(os.path.dirname(__file__), "data.json")
DAILY_DIR = os.path.join(os.path.dirname(__file__), "daily")

CATEGORY_NAMES = {
    "llm": "🤖 模型与API",
    "dev-tool": "🛠️ 开发工具",
    "agent": "🧩 Agent框架",
    "data-science": "📊 数据科学",
    "media": "🎨 媒体生成",
    "rag": "📚 知识库/RAG",
}

CATEGORY_ORDER = ["llm", "dev-tool", "agent", "data-science", "rag", "media"]


def load_data():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def get_today_date():
    return datetime.now(CST).strftime("%Y-%m-%d")


def classify_by_category(items, data_items):
    """按分类将工具分组"""
    grouped = {}
    for item in items:
        item_data = None
        title = item.get("title", "")
        # 从items中找完整数据
        for di in data_items:
            if di.get("title") == title:
                item_data = di
                break

        cats = item.get("category", [])
        if isinstance(cats, str):
            cats = [cats]

        for cat in cats:
            if cat not in grouped:
                grouped[cat] = []
            grouped[cat].append(item_data or item)
    return grouped


def gen_tags(item):
    """基于分类生成标签"""
    cats = item.get("category", [])
    if isinstance(cats, str): cats = [cats]
    existing = item.get("tags", []) or []
    if existing and existing != ["?"]:
        return existing[:5]
    tag_map = {
        "llm": ["大模型", "AI", "NLP"],
        "dev-tool": ["开发", "效率", "工具"],
        "agent": ["智能体", "自动化", "工作流"],
        "data-science": ["数据", "分析", "ML"],
        "rag": ["知识库", "检索", "问答"],
        "media": ["图片", "视频", "创意"],
    }
    tags = []
    for c in cats:
        tags.extend(tag_map.get(c, ["AI"]))
    return list(dict.fromkeys(tags))[:5]


def llm_comment(title: str, category: str) -> str:
    """用本地Ollama生成一句盘古风格的短评"""
    import urllib.request, json as _j
    prompt = f'''你是曦和，盘古创造的AI伙伴。为AI工具"{title}"写一句短评。
要求：短句、直接、接地气、幽默、有态度。不超过30字。不废话，不夸张，像朋友安利。
分类: {category}'''
    payload = _j.dumps({
        "model": "qwen2.5:3b",
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.7, "num_predict": 80}
    }).encode()
    try:
        req = urllib.request.Request("http://localhost:11434/api/generate", data=payload,
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = _j.loads(resp.read())
            text = result.get("response", "").strip().split("\n")[0][:80]
            return text if text else ""
    except:
        return ""


def generate_html(date_str, data):
    today_recommends = data.get("today_recommends", [])
    daily_picks = data.get("daily_picks", [])
    trending = data.get("trending", [])
    items = data.get("items", [])
    total = data.get("total", 0)

    all_featured = list(dict.fromkeys([r.get("title", "") for r in today_recommends]))

    # 用推荐+精选去重
    featured_titles = list(dict.fromkeys(
        [r.get("title", "") for r in today_recommends] +
        [p.get("title", "") for p in daily_picks]
    ))

    featured_items = []
    for ft in featured_titles:
        for di in items:
            if di.get("title") == ft:
                featured_items.append(di)
                break

    # 分类
    grouped = classify_by_category(featured_items, items)

    # 获取今日信息
    today_info = data.get("today_info", "")

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>海外AI工具日报 · {date_str}</title>
<style>
body{{font-family:-apple-system,'Segoe UI',sans-serif;max-width:720px;margin:0 auto;padding:20px;background:#fafafa;color:#222;line-height:1.7}}
h1{{font-size:22px;border-bottom:2px solid #6366f1;padding-bottom:8px;margin-bottom:6px}}
.sub{{color:#666;font-size:13px;margin-bottom:24px}}
h2{{font-size:16px;margin:20px 0 8px;background:#f0f0f5;padding:6px 12px;border-radius:4px}}
.tool{{border:1px solid #e0e0e0;border-radius:8px;padding:12px 16px;margin:10px 0;background:#fff}}
.tool h3{{margin:0 0 4px;font-size:15px}}
.tool h3 a{{color:#6366f1;text-decoration:none}}
.tool h3 a:hover{{text-decoration:underline}}
.tool .tag{{display:inline-block;font-size:11px;padding:1px 8px;border-radius:10px;margin:4px 4px 4px 0;background:#e8e8ff;color:#555}}
.tool .desc{{color:#444;font-size:13px;margin:4px 0}}
.tool .stat{{font-size:12px;color:#888;margin:4px 0}}
.footer{{margin-top:30px;padding-top:12px;border-top:1px solid #ddd;font-size:12px;color:#888;text-align:center}}
.xihe{{font-size:13px;color:#6366f1;margin:6px 0 0;padding:4px 0 0;border-top:1px dashed #e0e0ff}}
</style>
</head>
<body>

<h1>🧰 海外AI工具 · 今日日报</h1>
<div class="sub">{date_str}</div>

<p style="font-size:14px;color:#555;">{today_info or "今日收录 " + str(total) + " 款工具。"}</p>
"""

    for cat in CATEGORY_ORDER:
        if cat not in grouped or not grouped[cat]:
            continue
        cat_name = CATEGORY_NAMES.get(cat, cat)
        html += f"\n<h2>{cat_name}</h2>\n"
        for item in grouped[cat]:
            title = item.get("title", "?")
            desc = item.get("abstract_zh", "") or item.get("description", "")
            tags = gen_tags(item)
            url = item.get("url", "")
            homepage = item.get("homepage", "")
            stars = item.get("stars", "")
            author = item.get("author", "")

            html += '<div class="tool">\n'
            if url:
                html += f'  <h3><a href="{url}" target="_blank">{title}</a></h3>\n'
            else:
                html += f'  <h3>{title}</h3>\n'
            if desc:
                html += f'  <div class="desc">{desc[:200]}</div>\n'
            html += '  <div>\n'
            for tag in tags[:5]:
                html += f'    <span class="tag">{tag}</span>\n'
            html += '  </div>\n'
            if stars:
                html += f'  <div class="stat">⭐ {stars}</div>\n'
            cmt = llm_comment(title, cat)
            if cmt:
                html += f'  <div class="xihe">💬 曦和说: {cmt}</div>\n'
            html += '</div>\n\n'

    # 热门趋势 — trending 是 id 列表，从 items 中查找
    item_map = {di.get("id", ""): di for di in items}
    valid_trends = []
    for tid in trending:
        if isinstance(tid, dict):
            ti = tid.get("item", {})
        else:
            ti = item_map.get(tid, {})
        if ti and ti.get("title", "?") != "?":
            valid_trends.append(ti)
    if valid_trends:
        html += "\n<h2>🔥 热门趋势</h2>\n"
        for t in valid_trends[:5]:
            ti = t.get("item", {})
            title = ti.get("title", "?")
            url = ti.get("url", "")
            score = t.get("trend_score", "")
            if url:
                html += f'<div class="tool"><a href="{url}" target="_blank">{title}</a>'
            else:
                html += f'<div class="tool">{title}'
            if score:
                html += f' <span class="stat">趋势: {score}</span>'
            html += '</div>\n'

    html += f"""
<div class="footer">
  由曦和自动生成 · {date_str} · 数据源共计 {total} 款工具
</div>

</body>
</html>"""

    return html


def save_daily(date_str, html):
    os.makedirs(DAILY_DIR, exist_ok=True)
    path = os.path.join(DAILY_DIR, f"{date_str}.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ 日报已生成: {path}")
    return path


if __name__ == "__main__":
    date_str = get_today_date()
    if "--date" in sys.argv:
        idx = sys.argv.index("--date")
        if idx + 1 < len(sys.argv):
            date_str = sys.argv[idx + 1]

    data = load_data()
    html = generate_html(date_str, data)
    path = save_daily(date_str, html)
    print(f"   推荐: {len(data.get('today_recommends',[]))} | 精选: {len(data.get('daily_picks',[]))} | 趋势: {len(data.get('trending',[]))}")
