#!/usr/bin/env python3
"""generate_category_pages.py — 生成分类 SEO 落地页

为每个分类生成静态 HTML 页面（如 agent.html, llm.html 等），
让搜索引擎直接索引到分类页面，提高长尾搜索流量。

用法：python scripts/generate_category_pages.py
在日更管线中调用：可在 generate_sitemap.py 之后运行
"""

import json
import os
import sys

SITE_DIR = os.path.join(os.path.dirname(__file__), '..', 'site')
DATA_JSON = os.path.join(SITE_DIR, 'data.json')

# 分类中文名
CAT_NAMES = {
    'agent': ('Agent / 智能体工具', 'AI Agent 框架、多智能体系统、自动化代理 — 让 AI 替你干活'),
    'llm': ('大语言模型 / LLM', 'LLM 推理、微调、部署工具 — 大模型时代的瑞士军刀'),
    'dev-tool': ('开发者工具', 'IDE 插件、CLI 工具、代码生成 — 开发者的效率工具箱'),
    'rag': ('RAG / 检索增强生成', '知识库问答、文档检索、向量数据库 — 让 AI 连接你的数据'),
    'media': ('多模态 / 媒体', '文生图、文生视频、音频处理 — 搞视觉和声音的人看过来'),
    'data-science': ('数据科学', '数据分析、可视化、MLOps — 数据工程师的日常'),
    'uncategorized': ('其他 AI 工具', '不好分类但值得一看的 AI 宝藏'),
}

# 分类在首页的 icon
CAT_ICONS = {
    'agent': '🤖', 'llm': '🧠', 'dev-tool': '🛠️',
    'rag': '📚', 'media': '🎨', 'data-science': '📊',
    'uncategorized': '📦',
}

TEMPLATE = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{icon} {name_zh} · AIbounty</title>
<meta name="description" content="{desc} — AIbounty 收录 {count} 个相关工具，每日更新。">
<link rel="canonical" href="https://www.aibounty.cn/{slug}">
<!-- 百度自动推送 -->
<script>
(function(){{var bp=document.createElement('script');bp.src='https://zz.bdstatic.com/linksubmit/push.js';bp.async=true;var s=document.getElementsByTagName('script')[0];s.parentNode.insertBefore(bp,s);}})();
</script>
<!-- 百度统计 -->
<script>
var _hmt = _hmt || [];
(function(){{var hm=document.createElement('script');hm.src='https://hm.baidu.com/hm.js?5af31489d2c04d8f7b0bc8a8c852bcf2';var s=document.getElementsByTagName('script')[0];s.parentNode.insertBefore(hm,s);}})();
</script>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
:root{{--bg:#0a0e17;--card:#111827;--border:#1e3a5f;--text:#f1f5f9;--text2:#94a3b8;--text3:#64748b;--primary:#3b82f6;--accent:#f59e0b}}
body{{font-family:-apple-system,BlinkMacSystemFont,'PingFang SC','Microsoft YaHei',sans-serif;background:var(--bg);color:var(--text);-webkit-font-smoothing:antialiased}}
.nav{{position:fixed;top:0;left:0;right:0;z-index:100;background:rgba(10,14,23,0.75);backdrop-filter:blur(20px);border-bottom:1px solid rgba(30,58,95,0.4)}}
.nav-inner{{max-width:1200px;margin:0 auto;display:flex;align-items:center;justify-content:space-between;padding:0 24px;height:60px}}
.nav-brand{{color:var(--text);text-decoration:none;font-size:18px;font-weight:700}}
.nav-links{{display:flex;gap:12px}}
.nav-link{{color:var(--text2);text-decoration:none;font-size:14px;transition:color 0.15s}}
.nav-link:hover{{color:var(--primary)}}
.container{{max-width:1200px;margin:0 auto;padding:80px 24px 40px}}
.header{{margin:32px 0 24px}}
.header h1{{font-size:28px;margin-bottom:8px}}
.header p{{color:var(--text2);font-size:15px;line-height:1.6}}
.stats{{display:flex;gap:16px;margin:16px 0 32px;flex-wrap:wrap}}
.stat-card{{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:16px 24px;text-align:center}}
.stat-card .num{{font-size:24px;font-weight:700;color:var(--primary)}}
.stat-card .label{{font-size:12px;color:var(--text3);margin-top:4px}}
.tool-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:16px}}
.tool-card{{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:20px;transition:all 0.15s;text-decoration:none;color:var(--text);display:block}}
.tool-card:hover{{border-color:var(--primary);transform:translateY(-2px);box-shadow:0 4px 20px rgba(59,130,246,0.15)}}
.tool-card h3{{font-size:15px;margin-bottom:8px;line-height:1.4}}
.tool-card .desc{{font-size:13px;color:var(--text2);line-height:1.5;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}}
.tool-card .meta{{display:flex;align-items:center;gap:12px;margin-top:10px;font-size:12px;color:var(--text3)}}
.tag{{display:inline-block;background:rgba(59,130,246,0.1);color:var(--primary);padding:2px 10px;border-radius:4px;font-size:11px;margin-right:4px}}
.back-home{{display:inline-block;margin-top:32px;color:var(--text2);text-decoration:none;font-size:14px}}
.back-home:hover{{color:var(--primary)}}
</style>
</head>
<body>
<div class="nav">
  <div class="nav-inner">
    <a href="/" class="nav-brand">🏴‍☠️ AIbounty</a>
    <div class="nav-links">
      <a href="/daily.html" class="nav-link">📰 日报</a>
      <a href="/about.html" class="nav-link">ℹ️ 关于</a>
    </div>
  </div>
</div>
<div class="container">
  <div class="header">
    <h1>{icon} {name_zh}</h1>
    <p>{desc}</p>
    <div class="stats">
      <div class="stat-card">
        <div class="num">{count}</div>
        <div class="label">收录工具</div>
      </div>
      <div class="stat-card">
        <div class="num">{high_stars}</div>
        <div class="label">高星项目</div>
      </div>
    </div>
  </div>
  <div class="tool-grid">
{tools_html}
  </div>
  <a href="/" class="back-home">← 返回首页</a>
</div>
<!-- JSON-LD -->
<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"CollectionPage","name":"{name_zh}","description":"{desc}","url":"https://www.aibounty.cn/{slug}","numberOfItems":{count}}}
</script>
</body>
</html>'''


def truncate(text, length=80):
    if not text:
        return ''
    text = str(text).replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
    return text[:length] + ('...' if len(text) > length else '')


def safe_print(msg):
    try:
        print(msg)
    except UnicodeEncodeError:
        print(str(msg).encode('utf-8', errors='replace').decode('gbk', errors='replace'))


def main():
    with open(DATA_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)
    items = data.get('items', [])
    total = len(items)

    # Group tools by category
    categorized = {}
    for it in items:
        cats = it.get('category', [])
        if isinstance(cats, str):
            cats = [cats]
        tid = it.get('id')
        if not tid:
            continue
        # For uncategorized, put if no category or "uncategorized"
        if not cats or 'uncategorized' in cats:
            categorized.setdefault('uncategorized', []).append(it)
        else:
            for cat in cats:
                if cat in CAT_NAMES:
                    categorized.setdefault(cat, []).append(it)

    generated = 0
    for cat_slug, cat_info in CAT_NAMES.items():
        name_zh, desc = cat_info
        cat_tools = categorized.get(cat_slug, [])
        icon = CAT_ICONS.get(cat_slug, '📦')
        count = len(cat_tools)
        high_stars = sum(1 for t in cat_tools if int(t.get('score', 0) or 0) > 1000)

        if count == 0:
            continue

        # Sort by score descending
        cat_tools.sort(key=lambda t: int(t.get('score', 0) or 0), reverse=True)

        # Build tool cards
        cards = []
        for t in cat_tools[:100]:  # Top 100 per page
            title = (t.get('title') or 'Unknown')[:60]
            zh_abs = t.get('abstract_zh', '') or t.get('abstract', '') or ''
            score = int(t.get('score', 0) or 0)
            stars = f'⭐ {score}' if score else ''
            sfmt = f'{score/1000:.1f}k' if score >= 1000 else str(score) if score else ''
            date = (t.get('captured_at', '') or '')[:10]
            tags = t.get('data_tags', []) or []
            tags_html = ''.join(f'<span class="tag">{truncate(tag, 20)}</span>' for tag in tags[:3])

            card = f'''    <a href="tool.html?id={t["id"]}" class="tool-card">
      <h3>{truncate(title, 60)}</h3>
      <div class="desc">{truncate(zh_abs, 120)}</div>
      <div class="meta">
        {sfmt and f'<span>{stars}</span>' or ''}
        {date and f'<span>{date}</span>' or ''}
      </div>
      <div style="margin-top:6px">{tags_html}</div>
    </a>'''
            cards.append(card)

        tools_html = '\n'.join(cards)

        # Generate page
        html = TEMPLATE.format(
            icon=icon, name_zh=name_zh, desc=desc, count=count,
            high_stars=high_stars, slug=f'{cat_slug}.html',
            tools_html=tools_html,
        )

        out_path = os.path.join(SITE_DIR, f'{cat_slug}.html')
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(html)
        generated += 1
        safe_print(f'[OK] {cat_slug}.html — {count} tools')

    safe_print(f'[OK] Generated {generated} category pages')
    return 0


if __name__ == '__main__':
    sys.exit(main())
