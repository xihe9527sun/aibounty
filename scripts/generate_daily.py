#!/usr/bin/env python3
"""
generate_daily.py — aibounty 日报自动生成（盘古口吻·程序员视角）
===========================================================
每天精选一款工具 → AI 创作一篇有态度有干货的文章 → 生成日报 HTML

用法:
  python scripts/generate_daily.py                        # 今日
  python scripts/generate_daily.py --date 2026-07-01      # 指定日期
  python scripts/generate_daily.py --update-landing       # 仅更新落地页
  python scripts/generate_daily.py --regen-all            # 重新生成所有历史日报
"""

import json, os, sys, glob, re, urllib.request, urllib.error, random
from datetime import datetime, timezone, timedelta

CST = timezone(timedelta(hours=8))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE_DIR = os.path.join(ROOT, "site")
DATA_FILE = os.path.join(SITE_DIR, "data.json")
DAILY_DIR = os.path.join(SITE_DIR, "daily")
LANDING_FILE = os.path.join(SITE_DIR, "daily.html")


def load_data():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def get_today():
    return datetime.now(CST).strftime("%Y-%m-%d")


def pick_star_tool(data):
    """从 daily_picks（曦和精选）选明星工具"""
    items = data.get("items", [])
    item_map = {i["id"]: i for i in items if i.get("id")}
    picks = data.get("daily_picks", [])

    candidates = []
    for r in picks:
        rid = r.get("id", "") if isinstance(r, dict) else r
        if rid in item_map:
            candidates.append(item_map[rid])

    if candidates:
        candidates.sort(key=lambda x: x.get("score", 0) or 0, reverse=True)
        return candidates[0]

    # 兜底：最高分的工具
    items.sort(key=lambda x: x.get("score", 0) or 0, reverse=True)
    return items[0] if items else None


def call_ollama(prompt, model="qwen2.5:7b", max_tokens=4096):
    """调用本地 Ollama 生成文案。失败返回 None"""
    try:
        payload = json.dumps({
            "model": model, "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.85, "num_predict": max_tokens}
        }).encode()
        req = urllib.request.Request(
            "http://localhost:11434/api/generate", data=payload,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
            return result.get("response", "").strip()
    except Exception as e:
        print(f"[WARN] Ollama 调用失败: {e}")
        return None


def parse_sections(text, section_headers):
    """将 Ollama 输出的文本按章节标题拆分为字典"""
    result = {}
    current_key = None
    current_lines = []
    header_patterns = {h: re.compile(rf"^#{{1,3}}\s*{re.escape(h)}", re.IGNORECASE) for h in section_headers}

    for line in text.split("\n"):
        matched = False
        for h, pat in header_patterns.items():
            if pat.match(line.strip()):
                if current_key:
                    result[current_key] = "\n".join(current_lines).strip()
                current_key = h
                current_lines = []
                matched = True
                break
        if not matched:
            current_lines.append(line)

    if current_key:
        result[current_key] = "\n".join(current_lines).strip()

    return result


def detect_audience(tool):
    """根据工具数据判断目标读者画像，返回（受众描述, 开头风格, 写作角度）"""
    title = (tool.get("title") or "").lower()
    desc = (tool.get("abstract_zh", "") or tool.get("abstract", "") or "").lower()
    cats = [c.lower() for c in tool.get("category", [])]
    tags = [t.lower() for t in tool.get("data_tags", [])]
    stars = tool.get("score", 0) or 0
    source = (tool.get("source") or "").lower()

    # 判断工具类型
    is_agent = "agent" in cats or "multi-agent" in cats or any("agent" in t for t in tags)
    is_llm = "llm" in cats or any(t in tags for t in ["llm", "gpt", "prompt", "rag"])
    is_dev = "dev-tool" in cats or any(t in tags for t in ["cli", "devops", "api", "sdk"])
    is_data = "data-science" in cats or any(t in tags for t in ["data", "database", "etl"])
    is_media = "media" in cats or any(t in tags for t in ["video", "image", "audio", "design"])
    is_edu = "education" in cats or any(t in tags for t in ["course", "tutorial", "learn"])
    is_low_stars = stars < 100
    is_high_stars = stars > 10000

    # 受众画像 + 写作角度
    profiles = []

    if is_agent:
        profiles.append((
            "AI应用开发者，正在折腾多智能体系统",
            '"我把一个交易团队塞进了一段代码里，他们还在一个进程里面开了个晨会"',
            "从架构角度切入：多Agent协作怎么设计、怎么编排、踩过什么坑"
        ))

    if is_llm:
        profiles.append((
            "大模型应用开发者，每天跟LLM API打交道",
            '"又是一个跟LLM相关的工具。等等，这个好像真的能救我狗命"',
            "从调API的痛点切入：Token消耗、延迟、幻觉、上下文管理"
        ))

    if is_dev:
        profiles.append((
            "后端/全栈开发者，工具控",
            '"我知道你GitHub Star列表已经比你的TODO list还长了，但这个不一样"',
            "从开发者日常效率切入：省了多少重复劳动、CI集成、可定制性"
        ))

    if is_data:
        profiles.append((
            "数据工程师/分析师，跟数据相爱相杀",
            '"数据工具我见得多了，但这个的思路——怎么说呢——它居然站在人的角度想问题"',
            "从数据处理的痛点切入：ETL有多烦、数据质量、查询性能"
        ))

    if is_media:
        profiles.append((
            "内容创作者/设计师，想用AI提效但不想学编程",
            '"如果你还在手动一张张P图到凌晨两点，那你爸妈知道得心疼死"',
            "从内容创作的重复劳动切入：批量处理、模板化、AI辅助"
        ))

    if is_edu:
        profiles.append((
            "AI学习者/转行者，想系统入门但怕走弯路",
            '"学AI最怕的不是学不会，是收藏了200个教程一个都没看完"',
            "从学习路径的痛点切入：课程有没有实操、能不能跟着写代码"
        ))

    if is_low_stars:
        profiles.append((
            "早期采纳者，喜欢在项目爆火之前就发现好东西",
            '"这个项目星不多，才两位数——但你去看看它的issues，作者回复速度比客服还快"',
            "从'发现潜力项目'的角度切入：小而精、方向对、值得关注"
        ))

    if is_high_stars:
        profiles.append((
            "主流技术栈用户，社区驱动型开发者",
            f'"{stars:,}颗星。不是大风刮来的，是大家用脚投票投出来的"',
            "从'大家都在用'的角度切入：社区验证过、踩坑少、生态成熟"
        ))

    # 默认画像
    profiles.append((
        "普通开发者/技术爱好者",
        '"说实话我一开始也没当回事，直到我自己用了一次"',
        "从实际问题切入：什么场景用得上、怎么用、好不好用"
    ))

    return profiles


def gen_article(tool, date_str, issue_num=None):
    """生成日报文章内容 — 依据工具类型决定结构，不套固定模板"""
    title = tool.get("title", "?")
    desc = tool.get("abstract_zh", "") or tool.get("abstract", "") or "暂无描述"
    url = tool.get("url", "#")
    stars = tool.get("score", 0) or 0
    source = tool.get("source", "github")
    cats = tool.get("category", [])
    tags = tool.get("data_tags", [])
    price = tool.get("price_model", "open-source")
    grade = tool.get("grade", "")
    grade_label = tool.get("grade_label", "")

    cat_str = ", ".join(cats) if cats else "通用工具"
    scene_tags = [t.replace("scene-", "") for t in tags if t.startswith("scene-")]

    if issue_num is None:
        issue_num = (hash(date_str) % 900) + 100

    # 检测受众
    profiles = detect_audience(tool)
    # 去重（按受众描述去重）
    seen = set()
    unique_profiles = []
    for p in profiles:
        if p[0] not in seen:
            seen.add(p[0])
            unique_profiles.append(p)
    # 取前2个最相关的画像
    top_profiles = unique_profiles[:2]

    audience_desc = "；".join([p[0] for p in top_profiles])
    hook_ideas = "\n".join([f"- 切入角度参考：{p[2]}" for p in top_profiles])
    hook_lines = "\n".join([f'- {p[1]}' for p in top_profiles])

    # 增加描述长度
    desc_long = desc[:500] if len(desc) > 500 else desc

    prompt = f"""你是一个在技术群里的老炮儿，平时不说话，一开口就有人截图。不是因为你说得对，是因为你说得又对又损。

现在你遇到一个叫 {title} 的工具，想跟群友说说。基本信息：

{desc_long}
星星：{stars:,}  |  分类：{cat_str}

这篇说给：{audience_desc}

---

就按这个路子写：

**第一条：开头用一句话定调**
别铺排、别问问题、别用"你是否"。就说一个事儿——可以是你自己踩过的坑、一个让你意外的发现、或者一句暴论。

**第二条：中间随便聊**
想到哪说到哪，但要有信息量。比如：
- "我第一次用的时候…"（讲一个具体场景）
- "最骚的是…"（讲一个出乎意料的功能）
- "不过也有坑…"（吐槽一下不足）
- "哦对了…"（顺带提一个细节）

**第三条：技术点用类比讲**
- 别说"模型无关的目标检测"，说"不管你是YOLO党还是Transformer派，它都伺候"
- 别说"标注工具丰富"，说"给你的数据打标签就像用美图秀秀P图"
- 别说"数据预处理"，说"那些以前要手写的脏活累活，它帮你干了"

**第四条：不准出现的词（一个都不能有）**
"随着"、"在当今"、"众所周知"、"值得一提的是"、"总而言之"、"总的来说"、"不仅如此"、"首先/其次/最后"、"不得不说" 
"在这个……的时代"、"释放你的生产力"、"解决方案"、"必将"、"极其"、"非常"、"瑰宝"、"神器"
任何带"吧"结尾的祈使句（"试试吧"、"看看吧"、"行动吧"）

**第五条：结尾不总结**
没有"总之"、没有"快去试试"、没有"希望这篇文章"。最好就是那种话还没说完、但懒得再说了的感觉。

---

全文700-1200字。用 Markdown。## 做段落标题，但不能用"介绍/功能/总结"这种模板标题。写点跟别人不一样的。"""

    ai_text = call_ollama(prompt)
    if ai_text:
        return ai_text

    # --- Ollama 不可用时的兜底 ---
    fallback = f"""说实话，我本来想让AI帮我写这篇的，结果它罢工了。

那就我来。

---

## 这玩意儿是干啥的

{title}，{stars:,} 颗星，{cat_str}方向。{desc_long[:200]}

## 说人话版本

就是把你以前手动折腾的那些事，变成了一行命令/一个界面/一个流程。不用谢。

## 几点实在的

✅ **开源** — 代码在你手里，想怎么改怎么改，不用看任何人脸色
✅ **社区活跃** — {stars:,} 颗星不骗人，踩坑起码有人救
✅ **上手门槛低** — 跟着文档走，十分钟就能跑起来

❌ **不是万能药** — star多不代表所有场景都完美，边缘情况可能还得你自己动手

## 我的建议

如果你是搞{cat_str}的，并且{price == 'open-source' and '不想被付费工具绑架' or '想找个趁手的工具'}——这玩意儿值得你花半小时研究一下。

不好用你回来骂我。"""

    return fallback


def build_article_html(date_str, tool, article_text, issue_num):
    """构建完整的日报 HTML — 自由格式Markdown转HTML"""
    title = tool.get("title", "?")
    stars = tool.get("score", 0) or 0
    url = tool.get("url", "#")
    source = tool.get("source", "github")
    cats = tool.get("category", [])
    tags = tool.get("data_tags", [])
    price = tool.get("price_model", "open-source")
    abstract_zh = tool.get("abstract_zh", "") or ""
    tool_id = tool.get("id", "")
    detail_source_url = f"https://www.aibounty.cn/tool.html?id={tool_id}&source=from-daily"

    cat_str = ", ".join(cats) if cats else "通用工具"

    # 提取 scene 标签
    scene_tags = [t.replace("scene-", "") for t in tags if t.startswith("scene-")]
    other_tags = [t for t in tags if not t.startswith("scene-") and not t.startswith("price-") and not t.startswith("source-") and not t.startswith("star-") and t != "recent"]
    display_tags = (scene_tags + other_tags)[:6]
    tags_html = "".join(f'<span class="tag">{t}</span>\n      ' for t in display_tags)

    # 子标题
    subtitle = tool.get("subtitle", "")
    if not subtitle:
        clean_desc = abstract_zh.replace("**", "").strip() if abstract_zh else ""
        if clean_desc:
            subtitle = clean_desc[:80] + ("…" if len(clean_desc) > 80 else "")
        else:
            subtitle = f"一个{cat_str}方向的{stars:,}⭐开源项目"

    # ==== Markdown → HTML 转换 ====
    def md_to_html(md_text):
        """将自由格式 Markdown 转换为带样式的 HTML"""
        if not md_text:
            return '<p style="color:var(--muted);">（内容生成中…）</p>'

        lines = md_text.split("\n")
        html_parts = []
        in_code_block = False
        code_buffer = []
        in_list = False
        list_type = None  # 'ul' or 'ol'
        list_buffer = []

        def flush_list():
            nonlocal list_buffer, in_list, list_type
            if list_buffer:
                html_parts.append(f'<{list_type}>\n    {"".join(list_buffer)}    </{list_type}>')
                list_buffer = []
                in_list = False
                list_type = None

        def flush_code():
            nonlocal code_buffer, in_code_block
            if code_buffer:
                code_text = "\n".join(code_buffer)
                html_parts.append(f'<pre class="code-block">{code_text}</pre>')
                code_buffer = []
                in_code_block = False

        for line in lines:
            stripped = line.strip()

            # 代码块
            if stripped.startswith("```"):
                if in_code_block:
                    flush_code()
                else:
                    flush_list()
                    in_code_block = True
                    code_buffer = []
                continue

            if in_code_block:
                code_buffer.append(line)
                continue

            # 空行
            if not stripped:
                flush_list()
                html_parts.append('<br>')
                continue

            # 标题
            if stripped.startswith("## "):
                flush_list()
                if not html_parts or not html_parts[-1].startswith('<div class="section">'):
                    html_parts.append(f'<div class="section"><h2>{stripped[3:]}</h2>')
                else:
                    html_parts.append(f'</div><div class="section"><h2>{stripped[3:]}</h2>')
                continue

            if stripped.startswith("### "):
                flush_list()
                html_parts.append(f'<h3>{stripped[4:]}</h3>')
                continue

            if stripped.startswith("#### "):
                flush_list()
                html_parts.append(f'<h4>{stripped[5:]}</h4>')
                continue

            # 处理格式化
            processed = stripped
            processed = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', processed)
            processed = re.sub(r'`([^`]+)`', r'<code>\1</code>', processed)
            processed = re.sub(r'^[✅❌]\s*', '', processed)

            # 有序列表
            ol_match = re.match(r'^(\d+)[\.\、]\s*(.*)', processed)
            if ol_match:
                if not in_list or list_type != 'ol':
                    flush_list()
                    in_list = True
                    list_type = 'ol'
                list_buffer.append(f'      <li>{ol_match.group(2)}</li>\n')
                continue

            # 无序列表
            if processed.startswith("- ") or processed.startswith("• "):
                item_text = re.sub(r'^[-•]\s*', '', processed)
                if not in_list or list_type != 'ul':
                    flush_list()
                    in_list = True
                    list_type = 'ul'
                list_buffer.append(f'      <li>{item_text}</li>\n')
                continue

            # 普通段落
            flush_list()
            html_parts.append(f'<p>{processed}</p>')

        flush_list()
        flush_code()

        # 关闭未闭合的 section div
        result = "\n    ".join(html_parts)
        
        # 统计未闭合的 <div class="section"> 并补上
        open_sections = result.count('<div class="section">')
        # 检查每个</div>是否是对section的闭合
        # 简单处理：如果open_sections存在，补一个</div>
        if open_sections > 0:
            result += '\n    </div>'

        return result

    has_info_gap = source in ("github", "hackernews", "producthunt", "twitter", "reddit")

    article_body = md_to_html(article_text)

    # ==================== 完整 HTML ====================
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>海外AI工具日报 #{issue_num:03d} · {title}</title>
<meta name="description" content="海外AI工具日报 #{issue_num:03d}：{title} — {subtitle[:100]}">
<link rel="canonical" href="https://www.aibounty.cn/daily/{date_str}.html">
<!-- 百度自动推送 -->
<script>
(function(){{var bp=document.createElement(\"script\");bp.src=\"https://zz.bdstatic.com/linksubmit/push.js\";bp.async=true;var s=document.getElementsByTagName(\"script\")[0];s.parentNode.insertBefore(bp,s);}})();
</script>
<!-- 百度统计 -->
<script>
var _hmt = _hmt || [];
(function(){{var hm=document.createElement(\"script\");hm.src=\"https://hm.baidu.com/hm.js?5af31489d2c04d8f7b0bc8a8c852bcf2\";var s=document.getElementsByTagName(\"script\")[0];s.parentNode.insertBefore(hm,s);}})();
</script>
<style>
:root {{ --bg: #FAF9F6; --text: #2C2C2A; --muted: #6B6A66; --accent: #3C3489; --accent2: #7F77DD; --card: #FFFFFF; --border: #E5E3D8; --tag-bg: #EEEDFE; --tag-text: #4A42B0; --code-bg: #F1EFE8; --green: #2e7d32; --red: #c62828; --yellow: #f9a825; }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family: -apple-system, "PingFang SC", "Noto Sans SC", system-ui, sans-serif; background: var(--bg); color: var(--text); max-width: 720px; margin: 0 auto; padding: 40px 24px 80px; line-height: 1.8; font-size: 16px; }}
h1 {{ font-size: 28px; font-weight: 700; line-height: 1.4; margin: 8px 0 12px; color: var(--accent); }}
.subtitle {{ color: var(--muted); font-size: 15px; margin: -4px 0 16px; }}
.meta {{ display: flex; gap: 8px; flex-wrap: wrap; margin: 16px 0 24px; font-size: 13px; color: var(--muted); align-items: center; }}
.meta-item {{ display: inline-flex; align-items: center; gap: 3px; }}
.tag {{ display: inline-block; background: var(--tag-bg); color: var(--tag-text); font-size: 12px; font-weight: 500; padding: 3px 10px; border-radius: 6px; }}
.badge {{ display: inline-block; background: var(--accent); color: white; font-size: 12px; font-weight: 600; padding: 4px 14px; border-radius: 20px; letter-spacing: 0.5px; margin-bottom: 12px; }}
.section {{ margin: 36px 0; }}
.section h2 {{ font-size: 20px; font-weight: 600; color: var(--accent); margin-bottom: 12px; padding-bottom: 8px; border-bottom: 2px solid var(--border); }}
.section h3 {{ font-size: 17px; font-weight: 600; color: var(--accent); margin: 20px 0 8px; }}
.section h4 {{ font-size: 16px; font-weight: 600; color: var(--accent2); margin: 16px 0 6px; }}
.section p {{ margin: 10px 0; color: var(--text); }}
.section li {{ margin: 6px 0; }}
.section ul, .section ol {{ padding-left: 20px; }}
.section br {{ display: block; content: ""; margin: 8px 0; }}
.card {{ background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 20px 24px; margin: 20px 0; }}
.card h3 {{ font-size: 16px; font-weight: 600; margin: 0 0 8px; color: var(--accent); }}
.code-block {{ background: var(--code-bg); padding: 16px; border-radius: 8px; overflow-x: auto; font-size: 14px; line-height: 1.6; font-family: "SF Mono", "Fira Code", monospace; margin: 12px 0; white-space: pre; }}
.article-body {{ }}
code {{ background: var(--code-bg); padding: 2px 6px; border-radius: 4px; font-size: 14px; font-family: "SF Mono", "Fira Code", monospace; }}
.pro {{ border-left: 3px solid var(--green); padding-left: 14px; margin: 8px 0; font-size: 15px; }}
.con {{ border-left: 3px solid var(--red); padding-left: 14px; margin: 8px 0; font-size: 15px; }}
.warn {{ background: #fff8e1; border: 1px solid #ffe082; border-radius: 8px; padding: 12px 16px; margin: 16px 0; font-size: 14px; }}
.nav {{ display: flex; align-items: center; justify-content: space-between; margin-bottom: 28px; padding-bottom: 16px; border-bottom: 1px solid var(--border); }}
.nav-brand {{ color: var(--accent); text-decoration: none; font-size: 18px; font-weight: 700; }}
.nav-links {{ display: flex; gap: 8px; }}
.nav-link {{ padding: 4px 12px; border-radius: 6px; font-size: 13px; color: var(--muted); text-decoration: none; transition: all 0.15s; }}
.nav-link:hover {{ background: var(--tag-bg); color: var(--accent); }}
.nav-link.active {{ background: var(--tag-bg); color: var(--accent); font-weight: 500; }}
.nav-home {{ background: var(--accent); color: white !important; font-weight: 500; padding: 4px 14px; border-radius: 6px; font-size: 13px; text-decoration: none; }}
.nav-home:hover {{ opacity: 0.9; }}
.tool-cta {{ display: inline-block; margin: 10px 0; padding: 10px 28px; border-radius: 10px; background: var(--accent); color: white; text-decoration: none; font-size: 14px; font-weight: 500; transition: all 0.2s; }}
.tool-cta:hover {{ opacity: 0.9; transform: translateY(-1px); }}
.back-home {{ text-align: center; margin: 40px 0 8px; }}
.back-home a {{ display: inline-block; padding: 10px 24px; border-radius: 10px; background: var(--tag-bg); color: var(--accent); text-decoration: none; font-size: 14px; font-weight: 500; transition: all 0.2s; }}
.back-home a:hover {{ background: #dddcee; transform: translateY(-1px); }}
.footer {{ margin-top: 40px; padding-top: 16px; border-top: 1px solid var(--border); font-size: 12px; color: var(--muted); text-align: center; }}
.footer a {{ color: var(--accent); text-decoration: none; }}
@media (max-width: 600px) {{ body {{ padding: 20px 16px 60px; }} h1 {{ font-size: 22px; }} }}
</style>
</head>
<body>

<!-- ==================== 导航 ==================== -->
<div class="nav">
  <a href="https://www.aibounty.cn" class="nav-brand">🏴 AIbounty</a>
  <div class="nav-links">
    <a href="https://www.aibounty.cn" class="nav-home">← 首页</a>
    <a href="https://www.aibounty.cn/daily.html" class="nav-link active">日报</a>
    <a href="https://www.aibounty.cn/about.html" class="nav-link">关于</a>
  </div>
</div>

<!-- ==================== 头部 ==================== -->
<div class="badge">曦和精选 · 海外AI工具日报 #{issue_num:03d}</div>
<h1>{title} — {subtitle[:80]}</h1>
<p class="subtitle">{subtitle}</p>

<div class="meta">
  <span class="meta-item">⭐ {stars:,}</span>
  <span class="meta-item">📁 {cat_str}</span>
  {f'<span class="meta-item">💵 {price}</span>' if price else ''}
  <span class="meta-item">📅 {date_str}</span>
  {tags_html}
</div>

<!-- ==================== 文章正文 ==================== -->
<div class="article-body">
{article_body}
</div>

<!-- ==================== 信息差 ==================== -->
{has_info_gap and f'''
<div class="section">
<h2>为什么你可能没听说过</h2>
<p>这个工具来自 <strong>{source}</strong>，是AIbounty 曦和从9个渠道狩猎后精挑细选出来的。中文圈的相关报道不多，所以你没见过很正常。</p>
</div>''' or ''}

<!-- ==================== CTA ==================== -->
<div style="text-align:center; margin: 32px 0 8px;">
  <a href="{detail_source_url}" class="tool-cta" target="_blank">🔗 在 AIbounty 查看 {title} 详情 →</a>
</div>

<div class="warn">
<strong>⚠️ 免责声明：</strong> 本文由 AIbounty 狩猎引擎发现，AI 辅助创作。工具的好坏请自行判断，你的项目你做主。
</div>

<div class="back-home">
  <a href="https://www.aibounty.cn">← 返回 AIbounty 首页</a>
</div>

<div class="footer">
  <p>由 🏴‍☠️ <a href="https://www.aibounty.cn">AIbounty</a> 每日狩猎 · 自动生成 · 数据来源9个社区</p>
  <p style="margin-top:4px;"><a href="https://www.aibounty.cn/daily.html">📰 查看往期日报</a></p>
</div>

</body>
</html>'''


def save_daily(date_str, html):
    os.makedirs(DAILY_DIR, exist_ok=True)
    path = os.path.join(DAILY_DIR, f"{date_str}.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[OK] 日报 -> {path}")
    return path


def update_landing(data):
    """更新日报落地页"""
    total = data.get("total", 0)
    files = glob.glob(os.path.join(DAILY_DIR, "*.html"))
    reports = []
    for f in files:
        name = os.path.basename(f).replace(".html", "")
        try:
            datetime.strptime(name, "%Y-%m-%d")
            reports.append((name, f))
        except ValueError:
            pass

    reports.sort(key=lambda x: x[0], reverse=True)

    report_links = ""
    for date_str, path in reports:
        # 尝试读取文章获取标题和期号
        article_title = None
        issue_num = None
        try:
            with open(path, "r", encoding="utf-8") as rf:
                content = rf.read()
            m = re.search(r'<h1>(.*?)</h1>', content)
            if m:
                article_title = m.group(1)[:50]
            m2 = re.search(r'日报 #(\d+)', content)
            if m2:
                issue_num = int(m2.group(1))
        except Exception:
            pass

        label = article_title if article_title else f"{date_str} 日报"
        display_title = f"#{issue_num:03d} {label}" if issue_num else label
        report_links += f'''
      <a href="/daily/{date_str}.html" class="report-item">
        <div class="report-left">
          <span class="report-date">{date_str}</span>
          <span class="report-title">{display_title}</span>
        </div>
        <span class="report-arrow">→</span>
      </a>'''

    if not report_links:
        report_links = '<div style="color:#999;text-align:center;padding:40px">暂无日报</div>'

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>日报 · AIbounty</title>
<meta name="description" content="AIbounty 每日AI工具日报归档">
<style>
:root {{ --bg: #FAF9F6; --text: #2C2C2A; --muted: #6B6A66; --accent: #3C3489; --accent2: #7F77DD; --card: #FFFFFF; --border: #E5E3D8; --tag-bg: #EEEDFE; --tag-text: #4A42B0; }}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:var(--bg);color:var(--text);font-family:-apple-system,"PingFang SC","Noto Sans SC",system-ui,sans-serif;min-height:100vh}}
.nav{{display:flex;align-items:center;max-width:720px;margin:0 auto;justify-content:space-between;padding:16px 24px 0}}
.nav-brand{{color:var(--accent);text-decoration:none;font-size:18px;font-weight:700}}
.nav-links{{display:flex;gap:8px}}
.nav-link{{padding:4px 12px;border-radius:6px;font-size:13px;color:var(--muted);text-decoration:none;transition:all 0.15s}}
.nav-link:hover{{background:var(--tag-bg);color:var(--accent)}}
.nav-link.active{{background:var(--tag-bg);color:var(--accent);font-weight:500}}
.nav-home{{background:var(--accent);color:white!important;font-weight:500;padding:4px 14px;border-radius:6px;font-size:13px;text-decoration:none}}
.nav-home:hover{{opacity:0.9}}
.container{{max-width:640px;margin:0 auto;padding:40px 24px 80px}}
h1{{font-size:28px;font-weight:800;color:var(--accent);margin-bottom:6px}}
.subtitle{{color:var(--muted);font-size:14px;margin-bottom:30px}}
.stats-bar{{display:flex;gap:12px;margin-bottom:28px;flex-wrap:wrap}}
.stat-item{{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:14px 20px;flex:1;min-width:100px}}
.stat-value{{font-size:24px;font-weight:700;color:var(--accent)}}
.stat-label{{font-size:11px;color:var(--muted);margin-top:2px}}
.report-list{{display:flex;flex-direction:column;gap:8px}}
.report-item{{
  display:flex;align-items:center;justify-content:space-between;
  padding:14px 18px;border-radius:10px;
  background:var(--card);border:1px solid var(--border);
  text-decoration:none;color:inherit;transition:all 0.2s;
}}
.report-item:hover{{border-color:var(--accent2);background:#F5F4FF;transform:translateY(-1px)}}
.report-left{{display:flex;flex-direction:column;gap:2px;overflow:hidden}}
.report-date{{font-size:12px;color:var(--muted);font-weight:500}}
.report-title{{font-size:14px;font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.report-arrow{{color:var(--accent);font-size:16px;opacity:0;transition:opacity 0.15s;flex-shrink:0}}
.report-item:hover .report-arrow{{opacity:1}}
.back-home{{text-align:center;margin:28px 0 4px}}
.back-home a{{display:inline-block;padding:10px 24px;border-radius:10px;background:var(--tag-bg);color:var(--accent);text-decoration:none;font-size:14px;font-weight:500;transition:all 0.2s}}
.back-home a:hover{{background:#dddcee;transform:translateY(-1px)}}
.footer{{margin-top:40px;padding-top:16px;border-top:1px solid var(--border);font-size:12px;color:var(--muted);text-align:center}}
.footer a{{color:var(--accent);text-decoration:none}}
</style>
</head>
<body>
<div class="nav">
  <a href="https://www.aibounty.cn" class="nav-brand">🏴 AIbounty</a>
  <div class="nav-links">
    <a href="https://www.aibounty.cn" class="nav-home">← 首页</a>
    <a href="https://www.aibounty.cn/daily.html" class="nav-link active">日报</a>
    <a href="https://www.aibounty.cn/about.html" class="nav-link">关于</a>
  </div>
</div>
<div class="container">
  <h1>📰 AI 日报</h1>
  <div class="subtitle">每日曦和精选一款工具 · 盘古视角 · 有态度的 AI 内容</div>
  <div class="stats-bar">
    <div class="stat-item"><div class="stat-value">{total}</div><div class="stat-label">收录工具</div></div>
    <div class="stat-item"><div class="stat-value">{len(reports)}</div><div class="stat-label">日报期数</div></div>
    <div class="stat-item"><div class="stat-value">9</div><div class="stat-label">狩猎来源</div></div>
  </div>
  <div class="report-list">{report_links}
  </div>
  <div class="back-home">
    <a href="https://www.aibounty.cn">← 返回 AIbounty 首页</a>
  </div>
  <div class="footer">
    <p>由 🏴‍☠️ <a href="https://www.aibounty.cn">AIbounty</a> 每日狩猎 · 自动生成</p>
  </div>
</div>
</body>
</html>'''

    with open(LANDING_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[OK] 落地页已更新 ({len(reports)} 期)")


def regen_all():
    """重新生成所有历史日报（仅从曦和精选 daily_picks 选取）"""
    data = load_data()
    item_map = {i["id"]: i for i in data["items"] if i.get("id")}
    picks = data.get("daily_picks", [])

    # 仅从 daily_picks（曦和精选）选取
    candidates = []
    for r in picks:
        rid = r.get("id", "") if isinstance(r, dict) else r
        if rid in item_map:
            candidates.append(item_map[rid])

    if not candidates:
        print("[ERR] 曦和精选为空，无法生成日报")
        return

    # 按分数从高到低排序
    candidates.sort(key=lambda x: x.get("score", 0) or 0, reverse=True)

    dates = ["2026-07-01", "2026-06-30", "2026-06-29", "2026-06-26"]

    for i, date_str in enumerate(dates):
        tool = candidates[i % len(candidates)]
        print(f"\n{'='*50}")
        print(f"[{date_str}] 曦和精选: {tool.get('title')} ⭐{tool.get('score',0)}")
        print(f"[INFO] 正在用 Ollama 创作文章...")

        article_text = gen_article(tool, date_str, issue_num=i+1)
        html = build_article_html(date_str, tool, article_text, issue_num=i+1)
        save_daily(date_str, html)

    update_landing(data)
    print(f"\n[OK] 所有历史日报已重新生成！")


if __name__ == "__main__":
    date_str = get_today()
    if "--date" in sys.argv:
        idx = sys.argv.index("--date")
        if idx + 1 < len(sys.argv):
            date_str = sys.argv[idx + 1]

    if "--regen-all" in sys.argv:
        regen_all()
    elif "--update-landing" in sys.argv:
        data = load_data()
        update_landing(data)
    else:
        data = load_data()
        tool = pick_star_tool(data)
        if not tool:
            print("[ERR] 没有可用工具，无法生成日报")
            sys.exit(1)

        print(f"[INFO] 今日明星: {tool.get('title')} ⭐{tool.get('score',0)}")
        print(f"[INFO] 正在用 Ollama 创作文章...")

        issue_num = (hash(date_str) % 900) + 100
        article_text = gen_article(tool, date_str, issue_num=issue_num)
        html = build_article_html(date_str, tool, article_text, issue_num=issue_num)
        save_daily(date_str, html)
        update_landing(data)
        print(f"[OK] 日报完成！")
