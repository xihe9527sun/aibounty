#!/usr/bin/env python3
"""
update_readme.py — GitHub README 每日自动更新
============================================
读取 data.json → 生成动态 README → 推送 GitHub

用法:
  python scripts/update_readme.py          # 更新 site/README.md
  python scripts/update_readme.py --push   # 更新 + git commit + push
"""

import json, os, sys, subprocess
from datetime import datetime, timezone, timedelta

CST = timezone(timedelta(hours=8))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE_DIR = os.path.join(ROOT, "site")
DATA_FILE = os.path.join(SITE_DIR, "data.json")
README_FILE = os.path.join(SITE_DIR, "README.md")


def load_data():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    data = load_data()
    items = data.get("items", [])
    total = data.get("total", len(items))
    updated_at = data.get("updated_at", datetime.now(CST).strftime("%Y-%m-%d %H:%M"))
    today = datetime.now(CST).strftime("%Y-%m-%d")
    
    # 统计
    open_source = sum(1 for i in items if i.get("price_model") == "open-source")
    paid = sum(1 for i in items if i.get("price_model") == "paid")
    
    # 来源统计
    sources = {}
    for i in items:
        s = i.get("source", "unknown")
        sources[s] = sources.get(s, 0) + 1
    sorted_sources = sorted(sources.items(), key=lambda x: x[1], reverse=True)
    
    # TOP 10 按 score 排序
    with_score = [(i.get("score", 0) or 0, i) for i in items if i.get("score")]
    with_score.sort(key=lambda x: x[0], reverse=True)
    top10 = with_score[:10]
    
    # 分类统计
    cat_counts = {}
    for i in items:
        for c in i.get("category", []):
            cat_counts[c] = cat_counts.get(c, 0) + 1
    sorted_cats = sorted(cat_counts.items(), key=lambda x: x[1], reverse=True)
    
    # 生成来源表格
    source_rows = "\n".join(
        f"| {s} | {c} |" for s, c in sorted_sources
    )
    
    # 生成 TOP 10
    top10_rows = ""
    for rank, (score, item) in enumerate(top10, 1):
        title = item.get("title", "?")
        url = item.get("url", "#")
        top10_rows += f"{rank}. [{title}]({url}) — ⭐ {score:,}\n"
    
    # 生成分类表格
    cat_names = {
        "llm": "🤖 模型与API", "dev-tool": "🛠️ 开发工具",
        "agent": "🧩 Agent框架", "data-science": "📊 数据科学",
        "media": "🎨 媒体生成", "rag": "📚 知识库/RAG",
    }
    cat_rows = "\n".join(
        f"| {cat_names.get(c, c)} | {c} |" for c, _ in sorted_cats
    )
    
    readme = f"""# AIbounty · AI 赏金猎人

> 每日狩猎全球最前沿的 AI 工具，一站式发现最新人工智能框架、Agent、LLM、开发工具。

[🌐 访问网站](https://www.aibounty.cn) | [📰 日报](https://www.aibounty.cn/daily.html) | [📡 RSS](https://www.aibounty.cn/feed.xml) | [📖 关于](https://www.aibounty.cn/about.html)

---

## 📊 实时数据

*最后更新: {updated_at}*

| 指标 | 数值 |
|------|------|
| 收录工具 | **{total}** |
| 数据来源 | **{len(sources)}** 个社区/平台 |
| 开源项目 | **{open_source}** |
| 付费工具 | **{paid}** |
| ← 右上角 Star | **支持我们** |

### 📡 来源分布

| 来源 | 数量 |
|------|------|
{source_rows}
| **合计** | **{total}** |

### 🏷️ 分类分布

| 分类 | 标识 |
|------|------|
{cat_rows}

### ⭐ 高星项目 TOP 10

{top10_rows}
## ✨ 功能亮点

- **🏴‍☠️ 自动狩猎** — 9大来源每日自动采集，AI 聚合并打分
- **🏷️ 智能标签** — 6层标签体系：子分类/技术雷达/场景/价格/来源/死链检测
- **🔍 AI 搜索** — 自然语言搜索 + 智能推荐 + 匹配理由
- **💰 价格识别** — 自动识别开源/付费模式
- **⚡ 死链检测** — 自动检测无效链接并标记
- **🌏 双语** — 中英双语界面 + 工具描述
- **📡 RSS/Atom Feed** — 支持 Feedly/Inoreader 等阅读器订阅

## 🛠️ 技术栈

- **前端**: 纯原生 JavaScript + CSS（零框架，极致性能）
- **后端**: FastAPI (Python)，薄后端，数据优先
- **数据**: 自动化流水线 狩猎→合并→分类→评分→部署
- **部署**: 腾讯云 COS + CDN
- **狩猎引擎**: Python 多源并行抓取

## 📂 目录结构

```
aibounty/
├── site/               # 前端站点（纯静态）
│   ├── index.html      # 首页
│   ├── tool.html       # 工具详情页
│   ├── admin.html      # 管理后台
│   ├── daily.html      # 日报落地页
│   ├── daily/          # 每日日报
│   ├── feed.xml        # RSS Feed
│   ├── atom.xml        # Atom Feed
│   ├── data.json       # 完整工具数据
│   └── css/
├── scripts/            # 数据流水线
│   ├── hunt_v4.py      # 多源狩猎引擎
│   ├── auto_tag_v2.py  # 智能标签系统
│   ├── generate_daily.py  # 日报生成
│   ├── generate_feed.py   # RSS/Atom Feed 生成
│   ├── update_readme.py   # README 自动更新
│   └── generate_sitemap.py
└── data/
    └── example.json    # 示例数据
```

## 🏴‍☠️ 狩猎渠道

- GitHub Trending · HackerNews · 掘金 · ProductHunt · Gitee · 少数派 · arXiv · LangChain · TechCrunch · The Verge

## 🔗 链接

- 网站: [https://www.aibounty.cn](https://www.aibounty.cn)
- 日报: [https://www.aibounty.cn/daily.html](https://www.aibounty.cn/daily.html)
- RSS: [https://www.aibounty.cn/feed.xml](https://www.aibounty.cn/feed.xml)
- 提交工具: [sponsor@aibounty.cn](mailto:sponsor@aibounty.cn)

## License

MIT

---

*🏴‍☠️ 由 AIbounty 自动更新 · {today}*
"""

    with open(README_FILE, "w", encoding="utf-8") as f:
        f.write(readme)
    print(f"[OK] README 已更新: {README_FILE}")
    
    # --push 模式
    if "--push" in sys.argv:
        try:
            # 检测是否已有 git 仓库
            git_dir = os.path.join(ROOT, ".git")
            if not os.path.exists(git_dir):
                print("[SKIP] 未检测到 git 仓库，跳过推送")
                return
            
            # 只 stage README.md
            subprocess.run(
                ["git", "add", "site/README.md"],
                cwd=ROOT, check=True, capture_output=True
            )
            subprocess.run(
                ["git", "commit", "-m", f"README auto-update {today}"],
                cwd=ROOT, check=True, capture_output=True
            )
            subprocess.run(
                ["git", "push"],
                cwd=ROOT, check=True, capture_output=True
            )
            print(f"[OK] README 已推送至 GitHub")
        except subprocess.CalledProcessError as e:
            print(f"[WARN] 推送失败: {e.stderr.decode() if e.stderr else 'unknown'}")
        except FileNotFoundError:
            print("[WARN] git 命令不可用")


if __name__ == "__main__":
    main()
