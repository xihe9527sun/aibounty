# ToolPilot 数据分析器 · v1
# 从狩猎数据自动生成可视化报告
# 用法: python sop/analyze.py
# 输出: site/report.html (数据看板)

import json, os, time
from pathlib import Path
from collections import Counter, defaultdict

BASE = Path("E:/ToolPilot")
PREY_DIR = BASE / "prey"
SITE_DIR = BASE / "site"
REPORT_FILE = SITE_DIR / "report.html"
DATA_REPORT = SITE_DIR / "data-report.json"
PREY_DIR.mkdir(parents=True, exist_ok=True)
SITE_DIR.mkdir(parents=True, exist_ok=True)

def load_all_prey():
    items = []
    for pf in sorted(PREY_DIR.glob("tp-*.json")):
        try:
            with open(pf, "r", encoding="utf-8") as f:
                items.append(json.load(f))
        except: pass
    return items

def build_report(items):
    if not items:
        return "<h1>暂无数据</h1>"

    # 基础统计
    total = len(items)
    sources = Counter(i.get("source", "unknown") for i in items)
    source_names = {"hn":"HackerNews","github":"GitHub","juejin":"掘金",
                    "producthunt":"ProductHunt","arxiv":"ArXiv",
                    "oschina":"OSChina","modelscope":"魔搭","gitee":"Gitee"}

    # 星数统计
    stars_list = [(i.get("title","?"), int(i.get("score",0)), i.get("source","")) for i in items if i.get("score")]
    stars_list.sort(key=lambda x: -x[1])

    # 分类统计
    categories = Counter()
    cat_map = {
        "agent": ("🤖 Agent", "#7C3AED"), "llm": ("🧠 LLM", "#2563EB"),
        "rag": ("🔗 RAG", "#059669"), "dev-tool": ("🛠 Dev Tool", "#D97706"),
        "image-video": ("🎨 媒体", "#DC2626"), "audio": ("🎵 音频", "#7C3AED"),
        "data-science": ("📊 数据", "#0891B2"), "open-source": ("🌍 开源", "#059669"),
        "mcp": ("🔌 MCP", "#9333EA")
    }
    for item in items:
        text = (item.get("title","") + " " + item.get("abstract","")).lower()
        for key in cat_map:
            if key in text:
                categories[key] += 1
                break  # 一个工具只分一个类

    # 高频词分析
    stopwords = {"the","a","an","and","or","for","of","to","in","is","it","on","with",
                 "that","this","by","as","at","from","be","are","was","we","its","has","new","can","not","your","all","you"}
    word_counter = Counter()
    for item in items:
        for w in (item.get("title","") + " " + item.get("abstract","")).lower().split():
            w = w.strip(",.!?:;'\"()[]{}").strip()
            if len(w) > 3 and w not in stopwords and w.isalpha():
                word_counter[w] += 1

    # 时间线 — 按小时统计
    hour_counter = Counter()
    for item in items:
        t = item.get("captured_at","")
        if t:
            hour_counter[t[11:13]] += 1

    # 来源颜色
    src_colors = {"hn":"#FF6B35","github":"#24292F","arxiv":"#B31B1B",
                  "producthunt":"#DA552F","juejin":"#1E80FF","oschina":"#C71D23",
                  "modelscope":"#F9D546","gitee":"#C71D23"}

    # ── 生成 HTML ──
    now = time.strftime("%Y-%m-%d %H:%M")
    cats_sorted = sorted(categories.items(), key=lambda x:-x[1])

    # 条形图: 来源分布
    src_max = max(sources.values()) if sources else 1
    src_bars = ""
    for src, cnt in sorted(sources.items(), key=lambda x:-x[1]):
        pct = cnt / total * 100
        color = src_colors.get(src, "#6366F1")
        label = source_names.get(src, src)
        src_bars += f"""
        <div class="bar-row">
            <div class="bar-label">{label}</div>
            <div class="bar-track">
                <div class="bar-fill" style="width:{pct:.1f}%;background:{color}"></div>
            </div>
            <div class="bar-value">{cnt}<span class="bar-pct">{pct:.0f}%</span></div>
        </div>"""

    # 条形图: 分类分布
    cat_bars = ""
    if cats_sorted:
        cat_max = max(c[1] for c in cats_sorted)
        for key, cnt in cats_sorted:
            label, color = cat_map.get(key, (key, "#6366F1"))
            pct = cnt / cat_max * 100
            cat_bars += f"""
            <div class="bar-row cat-row">
                <div class="bar-label">{label}</div>
                <div class="bar-track">
                    <div class="bar-fill" style="width:{pct:.1f}%;background:{color}"></div>
                </div>
                <div class="bar-value">{cnt}</div>
            </div>"""

    # Top 10 表格
    top_rows = ""
    medals = ["🥇","🥈","🥉","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]
    for i, (name, stars, src) in enumerate(stars_list[:10]):
        sc = src_colors.get(src, "#6366F1")
        if stars >= 1000000:
            fmt = f"{stars/1000000:.1f}M"
        elif stars >= 1000:
            fmt = f"{stars/1000:.1f}k"
        else:
            fmt = str(stars)
        top_rows += f"""
        <tr>
            <td class="rank">{medals[i] if i < 10 else i+1}</td>
            <td class="name">{name[:50]}</td>
            <td><span class="src-tag" style="background:{sc}">{source_names.get(src,src)}</span></td>
            <td class="stars">{fmt}</td>
        </tr>"""

    # 热词云 (用 inline SVG 模拟)
    word_str = ""
    if word_counter:
        top_words = word_counter.most_common(25)
        max_w = top_words[0][1]
        for w, c in top_words:
            size = 0.7 + (c / max_w) * 1.3
            opacity = 0.5 + (c / max_w) * 0.5
            word_str += f'<span class="word" style="font-size:{size:.1f}em;opacity:{opacity:.2f}">{w}</span> '

    # 时间线
    timeline_bars = ""
    if hour_counter:
        for h in sorted(hour_counter.keys()):
            cnt = hour_counter[h]
            max_h = max(hour_counter.values())
            ht = 20 + (cnt / max_h) * 100 if max_h else 20
            timeline_bars += f'<div class="tl-bar" style="height:{ht:.0f}px" title="{h}:00 ({cnt})"></div>'

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ToolPilot · 数据看板</title>
<style>
* {{margin:0;padding:0;box-sizing:border-box;}}
body {{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',system-ui,sans-serif;background:#0a0a0f;color:#e2e8f0;}}
.header {{background:linear-gradient(135deg,#0a0a1f,#1a0a2e);padding:60px 40px 40px;text-align:center;position:relative;overflow:hidden;}}
.header::before {{content:'';position:absolute;top:-50%;left:-50%;width:200%;height:200%;background:radial-gradient(circle at 30% 50%,rgba(99,102,241,0.08) 0%,transparent 50%),radial-gradient(circle at 70% 50%,rgba(139,92,246,0.05) 0%,transparent 50%);}}
.header h1 {{font-size:28px;font-weight:700;background:linear-gradient(135deg,#818cf8,#a78bfa);-webkit-background-clip:text;-webkit-text-fill-fill:transparent;background-clip:text;position:relative;letter-spacing:-0.5px;}}
.header h1 span {{background:linear-gradient(135deg,#818cf8,#a78bfa);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}}
.header .sub {{color:#94a3b8;font-size:14px;margin-top:8px;position:relative;}}
.stats {{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;max-width:900px;margin:-20px auto 0;padding:0 20px;position:relative;z-index:2;}}
.stat-card {{background:#13131f;border:1px solid #1e1e30;border-radius:12px;padding:20px;text-align:center;}}
.stat-card .num {{font-size:32px;font-weight:700;color:#818cf8;}}
.stat-card .label {{font-size:13px;color:#64748b;margin-top:4px;}}
.container {{max-width:1000px;margin:0 auto;padding:30px 20px 60px;}}
.section {{margin-bottom:40px;}}
.section-title {{font-size:18px;font-weight:600;color:#e2e8f0;margin-bottom:16px;padding-bottom:8px;border-bottom:1px solid #1e1e30;display:flex;align-items:center;gap:8px;}}
.section-title .badge {{font-size:12px;background:#1e1e30;color:#94a3b8;padding:2px 10px;border-radius:20px;}}
.section-sub {{font-size:13px;color:#64748b;margin-top:-12px;margin-bottom:16px;}}
.bar-row {{display:grid;grid-template-columns:140px 1fr 80px;align-items:center;gap:12px;margin-bottom:8px;}}
.bar-label {{font-size:13px;color:#94a3b8;text-align:right;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}}
.bar-track {{height:24px;background:#1a1a2e;border-radius:12px;overflow:hidden;}}
.bar-fill {{height:100%;border-radius:12px;transition:width 0.6s ease;min-width:4px;}}
.bar-value {{font-size:13px;font-weight:600;color:#e2e8f0;}}
.bar-pct {{font-size:11px;color:#64748b;margin-left:4px;font-weight:400;}}
.cat-row .bar-label {{font-size:14px;}}
table {{width:100%;border-collapse:collapse;}}
th {{text-align:left;font-size:12px;color:#64748b;text-transform:uppercase;padding:8px 12px;border-bottom:1px solid #1e1e30;}}
td {{padding:10px 12px;border-bottom:1px solid #1a1a2e;font-size:14px;}}
.rank {{font-size:16px;width:36px;}}
.name {{color:#e2e8f0;max-width:360px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}}
.stars {{color:#f59e0b;font-weight:600;}}
.src-tag {{display:inline-block;padding:2px 8px;border-radius:4px;font-size:11px;color:#fff;}}
.words {{display:flex;flex-wrap:wrap;gap:8px;padding:20px;background:#13131f;border-radius:12px;border:1px solid #1e1e30;}}
.word {{display:inline-block;color:#94a3b8;line-height:1.4;}}
.timeline {{display:flex;align-items:flex-end;gap:2px;height:120px;padding:10px 0;background:#13131f;border-radius:8px;justify-content:center;}}
.tl-bar {{width:20px;background:linear-gradient(to top,#818cf8,#a78bfa);border-radius:4px 4px 0 0;min-height:4px;transition:height 0.3s;}}
.footer {{text-align:center;padding:30px;color:#475569;font-size:12px;}}
@media (max-width:768px) {{.stats {{grid-template-columns:repeat(2,1fr);}} .bar-row {{grid-template-columns:100px 1fr 60px;}}}}
</style>
</head>
<body>

<div class="header">
    <h1><span>🛸 ToolPilot · 数据看板</span></h1>
    <p class="sub">基于 {total} 条狩猎数据自动生成 · {now}</p>
</div>

<div class="stats">
    <div class="stat-card"><div class="num">{total}</div><div class="label">🎯 工具总数</div></div>
    <div class="stat-card"><div class="num">{len(sources)}</div><div class="label">🌐 数据来源</div></div>
    <div class="stat-card"><div class="num">{sum(int(i.get('score',0)) for i in items if i.get('score'))//1000}k</div><div class="label">⭐ 总星数</div></div>
    <div class="stat-card"><div class="num">{len(stars_list)}</div><div class="label">📊 有评分数据</div></div>
</div>

<div class="container">
    <!-- 来源分布 -->
    <div class="section">
        <div class="section-title">📡 来源分布 <span class="badge">各渠道捕获量</span></div>
        <div class="section-sub">数据来自 {len(sources)} 个猎场，HN 和 GitHub 贡献最多</div>
        {src_bars}
    </div>

    <!-- 分类分布 -->
    <div class="section">
        <div class="section-title">🏷️ 技术分类 <span class="badge">AI Agent 占比最高</span></div>
        <div class="section-sub">按工具标题和描述自动分类</div>
        {cat_bars}
    </div>

    <!-- Top 10 -->
    <div class="section">
        <div class="section-title">🏆 热门排行 <span class="badge">按星数排序</span></div>
        <div class="section-sub">GitHub Star 数 / 社区热度</div>
        <table>
            <thead><tr><th></th><th>工具名称</th><th>来源</th><th>⭐ 热度</th></tr></thead>
            <tbody>{top_rows}</tbody>
        </table>
    </div>

    <!-- 热词 -->
    <div class="section">
        <div class="section-title">🔤 高频热词 <span class="badge">AI Agent / LLM / Open Source 主导</span></div>
        <div class="words">{word_str}</div>
    </div>

    <!-- 时间线 -->
    <div class="section">
        <div class="section-title">⏱ 狩猎时间线 <span class="badge">按小时分布</span></div>
        <div class="timeline">{timeline_bars}</div>
    </div>
</div>

<div class="footer">
    🛸 ToolPilot · 数据每日自动更新 · 狩猎数据来自 HN / GitHub / ArXiv / ProductHunt
</div>

</body>
</html>"""

    return html

def main():
    items = load_all_prey()
    html = build_report(items)
    REPORT_FILE.write_text(html, encoding="utf-8")
    print(f"✅ 数据看板: {REPORT_FILE} ({len(html)} bytes)")

    # 保存JSON数据（供前端调用）
    summary = {
        "total": len(items),
        "sources": dict(Counter(i.get("source","unknown") for i in items)),
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    DATA_REPORT.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ 数据摘要: {DATA_REPORT}")

if __name__ == "__main__":
    main()
