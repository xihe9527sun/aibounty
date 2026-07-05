#!/usr/bin/env python3
"""
AIbounty 内容素材工厂 v0.1 — AI 赏金猎人每日精选
狩猎 → 选Top5 → 获取GitHub元数据 → 生成可发布的内容素材包
"""

import json, os, time, html
from pathlib import Path
from datetime import datetime
from collections import defaultdict

SITE_DIR = Path("E:/ToolPilot/site")
OUTPUT_DIR = Path("E:/ToolPilot/content")
OUTPUT_DIR.mkdir(exist_ok=True)

# ── 读取最新狩猎数据 ──
def load_data():
    with open(SITE_DIR / "data.json", "r", encoding="utf-8") as f:
        return json.load(f)

# ── 获取GitHub仓库真实元数据（用API，比爬页面轻10倍） ──
def fetch_github_repo(full_name):
    """获取GitHub仓库的详细元数据"""
    import urllib.request
    url = f"https://api.github.com/repos/{full_name}"
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "AIbounty/1.0",
            "Accept": "application/vnd.github.v3+json"
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return None

# ── 获取README摘要 ──
def fetch_readme_summary(full_name):
    """获取README第一段内容"""
    import urllib.request, re
    url = f"https://api.github.com/repos/{full_name}/readme"
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "AIbounty/1.0",
            "Accept": "application/vnd.github.v3.raw"
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            text = resp.read().decode("utf-8", errors="replace")
            # 取前500字，去掉markdown标记
            text = re.sub(r'[#*`\[\]>|_-]', ' ', text)[:500]
            return text.strip()
    except:
        return None

# ── 生成内容素材包 ──
def generate_material_pack(items, repo_data_map):
    """生成一份可直接发布的内容素材"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # 生成HTML素材
    html_parts = [f"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><title>AIbounty 每日素材包 · {now}</title>
<style>
body {{
    font-family: -apple-system, BlinkMacSystemFont, sans-serif;
    background: #0a0a0f; color: #e1e1e6; max-width: 800px; margin: 0 auto; padding: 40px 20px;
}}
.header {{
    text-align: center; margin-bottom: 40px; padding: 30px;
    background: linear-gradient(135deg, #1a1a2e, #16213e); border-radius: 16px;
    border: 1px solid #2a2a3e;
}}
.header h1 {{ font-size: 24px; margin: 0; background: linear-gradient(135deg, #818cf8, #a78bfa); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
.header .sub {{ color: #94a3b8; font-size: 14px; margin-top: 8px; }}
.header .stats {{ display: flex; justify-content: center; gap: 20px; margin-top: 16px; font-size: 13px; color: #64748b; }}
.card {{
    background: #14141f; border-radius: 12px; padding: 24px; margin-bottom: 16px;
    border: 1px solid #1e1e30; transition: all 0.2s;
}}
.card:hover {{ border-color: #818cf8; transform: translateY(-1px); }}
.card-rank {{ display: inline-block; width: 28px; height: 28px; line-height: 28px; text-align: center;
    border-radius: 8px; font-weight: 700; font-size: 13px; margin-right: 10px; }}
.rank-1 {{ background: #ffd700; color: #000; }}
.rank-2 {{ background: #c0c0c0; color: #000; }}
.rank-3 {{ background: #cd7f32; color: #fff; }}
.rank-n {{ background: #1e1e30; color: #818cf8; }}
.card-title {{ font-size: 18px; font-weight: 600; margin: 8px 0 4px; }}
.card-title a {{ color: #e1e1e6; text-decoration: none; }}
.card-title a:hover {{ color: #818cf8; }}
.card-desc {{ color: #94a3b8; font-size: 14px; line-height: 1.6; margin: 8px 0; }}
.card-meta {{ display: flex; gap: 16px; font-size: 13px; color: #64748b; flex-wrap: wrap; margin-top: 12px; }}
.meta-item {{ display: flex; align-items: center; gap: 4px; }}
.tag {{ display: inline-block; padding: 2px 8px; border-radius: 6px; font-size: 11px;
    background: #1a1a2e; color: #818cf8; border: 1px solid #2a2a3e; }}
.source-hn {{ color: #ff6b35; }} .source-github {{ color: #58a6ff; }}
.source-arxiv {{ color: #ff6b35; }} .source-producthunt {{ color: #da552f; }}
.readme-box {{ background: #0d0d18; border-radius: 8px; padding: 12px; margin-top: 8px;
    font-size: 13px; color: #94a3b8; line-height: 1.5; border-left: 3px solid #818cf8; }}
.footer {{ text-align: center; color: #64748b; font-size: 12px; margin-top: 40px; padding-top: 20px; border-top: 1px solid #1e1e30; }}
.stats-row {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; margin: 20px 0; }}
.stat-box {{ background: #14141f; border-radius: 10px; padding: 16px; text-align: center; border: 1px solid #1e1e30; }}
.stat-num {{ font-size: 24px; font-weight: 700; color: #818cf8; }}
.stat-label {{ font-size: 12px; color: #64748b; margin-top: 4px; }}
</style></head><body>

<div class="header">
    <h1>🏴‍☠️ AIbounty 每日AI工具精选</h1>
    <div class="sub">{now} · 自动狩猎 · 真实数据</div>
</div>
"""]

    # 统计面板
    total = len(items)
    gh_total = sum(1 for i in items if i.get('source') == 'github')
    max_stars = max((repo_data_map.get(i.get('title',''), {}).get('stargazers_count', i.get('score', 0) or 0) for i in items), default=0)
    html_parts.append(f"""<div class="stats-row">
    <div class="stat-box"><div class="stat-num">{total}</div><div class="stat-label">今日捕获</div></div>
    <div class="stat-box"><div class="stat-num">{gh_total}</div><div class="stat-label">GitHub项目</div></div>
    <div class="stat-box"><div class="stat-num">{max_stars:,}</div><div class="stat-label">最高星数</div></div>
</div>""")

    # Top 5 卡片
    for idx, item in enumerate(items[:5], 1):
        title = item.get('title', '无标题')
        source = item.get('source', 'unknown')
        abstract = item.get('abstract', '') or ''
        url = item.get('url', '#')
        score = item.get('score', 0) or 0
        category = item.get('category', []) or []
        scene = item.get('scene', []) or []

        rank_class = f"rank-{idx}" if idx <= 3 else "rank-n"
        medals = {1: '🥇', 2: '🥈', 3: '🥉'}
        medal = medals.get(idx, f'#{idx}')

        source_labels = {'github': '⭐ GitHub', 'hn': '🌐 HN', 'arxiv': '📄 ArXiv', 'producthunt': '🚀 PH'}

        # 附加GitHub元数据
        extra = repo_data_map.get(title, {})
        stars = extra.get('stargazers_count', score if score > 0 else '?')
        forks = extra.get('forks_count', '?')
        lang = extra.get('language', '') or ''
        updated = extra.get('pushed_at', '')[:10] if extra.get('pushed_at') else ''
        about = extra.get('description', '') or abstract

        html_parts.append(f"""
<div class="card">
    <div style="display:flex;align-items:center;">
        <span class="card-rank {rank_class}">{medal}</span>
        <span style="font-size:12px;color:#64748b;">{source_labels.get(source, source)}</span>
        {f'<span style="margin-left:8px;font-size:11px;color:#818cf8;">⭐ {int(stars):,}</span>' if isinstance(stars, int) else ''}
    </div>
    <div class="card-title"><a href="{url}" target="_blank">{html.escape(title)}</a></div>
    <div class="card-desc">{html.escape(about[:300])}</div>
    <div class="card-meta">
        {f'<span class="meta-item">🔧 {lang}</span>' if lang else ''}
        {f'<span class="meta-item">🍴 {forks:,}</span>' if isinstance(forks, int) else ''}
        {f'<span class="meta-item">📅 {updated}</span>' if updated else ''}
        {''.join(f'<span class="tag">{c}</span>' for c in category[:3])}
        {''.join(f'<span class="tag">{s}</span>' for s in scene[:2])}
    </div>
</div>""")

    html_parts.append(f"""
<div class="footer">
    <p>📡 数据来源: HackerNews · GitHub · ArXiv · Product Hunt<br>
    自动生成于 {now} · 由 AIbounty 狩猎引擎驱动</p>
</div>
</body></html>""")

    # 同时生成MD版本
    md_lines = [f"# 🏴‍☠️ AIbounty 每日AI工具精选", f"**{now}** · 自动狩猎 · 真实数据\n", "---\n"]
    for idx, item in enumerate(items[:5], 1):
        title = item.get('title', '无标题')
        url = item.get('url', '#')
        medals = {1: '🥇', 2: '🥈', 3: '🥉'}
        medal = medals.get(idx, f'{idx}.')
        extra = repo_data_map.get(title, {})
        stars = extra.get('stargazers_count', item.get('score', '?'))
        desc = extra.get('description', '') or item.get('abstract', '') or ''

        md_lines.append(f"\n### {medal} [{title}]({url})")
        md_lines.append(f"> {desc[:200]}")
        if isinstance(stars, int):
            md_lines.append(f"⭐ {stars:,} stars")
        md_lines.append("")

    md_content = "\n".join(md_lines)

    # 写文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    html_path = OUTPUT_DIR / f"daily_pack_{timestamp}.html"
    md_path = OUTPUT_DIR / f"daily_pack_{timestamp}.md"

    with open(html_path, "w", encoding="utf-8") as f:
        f.write("".join(html_parts))
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    # 同步到网站目录，使用固定名称
    latest_html = SITE_DIR / "latest-pack.html"
    latest_html.write_text("".join(html_parts), encoding="utf-8")

    return html_path, md_path, len(items[:5])

# ── 主流程 ──
def main():
    print("🏴‍☠️ AIbounty 内容素材工厂 v0.1")
    print("-" * 40)

    # 1. 加载数据
    data = load_data()
    items = data.get("items", [])
    daily_picks = data.get("daily_picks", [])
    print(f"📊 数据加载: {len(items)} 条工具, {len(daily_picks)} 条精选")

    # 2. 按星数排序，取Top5 GitHub项目做深度分析
    gh_items = [i for i in items if i.get('source') == 'github' and i.get('score', 0) and int(i.get('score', 0)) > 100]
    gh_items.sort(key=lambda x: int(x.get('score', 0) or 0), reverse=True)

    # 取Top 10 + 每日精选去重
    candidates = daily_picks[:5]
    seen_titles = {c.get('title') for c in candidates}
    for item in gh_items:
        if len(candidates) >= 10: break
        if item.get('title') not in seen_titles:
            candidates.append(item)
            seen_titles.add(item.get('title'))

    # 最终只取5个
    picks = candidates[:5]
    print(f"🎯 选定 {len(picks)} 个工具进行深度采集")

    # 3. 获取GitHub元数据（只对GitHub项目）
    repo_data = {}
    for item in picks:
        title = item.get('title', '')
        if item.get('source') == 'github' and '/' in title:
            print(f"  📡 获取 {title} ...", end=" ")
            data = fetch_github_repo(title)
            if data:
                repo_data[title] = data
                print(f"✅ {data.get('stargazers_count', 0):,} stars")
            else:
                print("⚠ 跳过")
            time.sleep(0.5)  # 礼貌限速
        elif item.get('source') == 'arxiv':
            print(f"  📄 ArXiv: {title[:50]}... (不需要GitHub数据)")

    # 4. 生成素材
    print("\n📝 生成素材包...")
    html_path, md_path, count = generate_material_pack(picks, repo_data)
    print(f"  ✅ HTML: {html_path}")
    print(f"  ✅ MD:   {md_path}")
    print(f"\n📦 产出: {count} 个工具素材包")

    # 5. 打印摘要
    print("\n📋 今日精选:")
    for idx, item in enumerate(picks, 1):
        title = item.get('title', '无标题')
        src = item.get('source', '?')
        score = item.get('score', 0) or 0
        print(f"  {idx}. [{src}] {title} (⭐ {score:,})")

if __name__ == "__main__":
    main()
