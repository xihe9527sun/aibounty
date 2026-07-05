# AIbounty 狩猎脚本 v3 · 8源并行
# 猎场: HN + 掘金 + GitHub + ProductHunt + Reddit + HuggingFace + ArXiv + Gitee
# 设计目标: 覆盖其他导航站没盯的信息差源

import urllib.request, json, os, time, re, html
from pathlib import Path
from xml.etree import ElementTree

BASE = Path("E:/ToolPilot")
PREY_DIR = BASE / "prey"
REPORT_DIR = BASE / "reports"
PREY_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

AI_KW = ["ai ", "gpt", "llm", "agent", "chatgpt", "claude", "copilot",
         "人工智能", "大模型", "AI工具", "深度学习", "机器学习",
         "openai", "anthropic", "mistral", "gemini", "deepseek",
         "transformer", "rag", "embedding", "vector", "neural"]

def _u(text):
    """安全unescape，避免变量名冲突"""
    try: return html.unescape(str(text))
    except: return str(text)

# ── 工具函数 ──────────────────────────────────────

def save_prey(source, title, abstract="", url="", score=0):
    """保存猎物前先过质量门——一次不中，百次不用"""
    # ── 质量门：不符合标准就不引入 ──
    if not url or not url.startswith("http"):
        print(f"  ⛔ {source}: {title[:40]}… → 无有效外部链接")
        return None
    if not abstract or len(abstract.strip()) < 5:
        print(f"  ⛔ {source}: {title[:40]}… → 无有效描述")
        return None
    thresholds = {"github": 100, "hn": 5, "producthunt": 3}
    min_score = thresholds.get(source, 1)
    if int(score or 0) < min_score:
        print(f"  ⛔ {source}: {title[:40]}… → 分数未达标 ({score} < {min_score})")
        return None
    if len(title.strip()) < 8:
        print(f"  ⛔ {source}: {title[:40]}… → 标题过短")
        return None

    fname = f"tp-{source}-{int(time.time()*1000)}-{os.urandom(2).hex()}.json"
    data = {
        "source": source, "title": title.strip()[:120],
        "abstract": (abstract or "")[:300],
        "url": url, "score": score,
        "captured_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    path = PREY_DIR / fname
    with open(str(path), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  ✅ {source}: {title[:50]}")
    return path

def fetch_json(url, timeout=15, data=None):
    headers = {"User-Agent": "AIbounty/3.0 (AI tools hunter; +https://aibounty.cn)"}
    if data:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers)
    return json.loads(urllib.request.urlopen(req, timeout=timeout).read())

def fetch_text(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8", errors="replace")

def is_matched(text, keywords=AI_KW):
    """检查文本是否命中AI关键词"""
    if not text: return False
    t = text.lower()
    return any(kw in t for kw in keywords)

def get_existing_titles(source):
    """获取已有猎物标题（去重用）"""
    titles = set()
    for pf in PREY_DIR.glob(f"tp-{source}-*.json"):
        try:
            with open(pf, "r", encoding="utf-8") as f:
                titles.add(json.load(f).get("title", ""))
        except: pass
    return titles


# ═══════════════════════════════════════════════════
# 猎场1: HackerNews
# ═══════════════════════════════════════════════════

def hunt_hn():
    """HN 最新AI工具帖（比 topstories 更快抓到新东西）"""
    count = 0
    try:
        # 用 newstories 而非 topstories — 更早发现
        ids = fetch_json("https://hacker-news.firebaseio.com/v0/newstories.json")[:50]
        existing = get_existing_titles("hn")
        for sid in ids:
            item = fetch_json(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json")
            title = item.get("title", "")
            if not title or title in existing: continue
            if is_matched(title):
                # 过滤非工具讨论帖
                tl = title.lower()
                if any(tl.startswith(p) for p in ('show hn:', 'ask hn:', 'tell hn:', 'launch hn:')):
                    print(f"  ⏭ HN讨论帖跳过: {title[:50]}")
                    continue
                text = item.get("text", "")[:200]
                if 'hn discussion' in (text or '').lower() and len(text or '') < 30:
                    print(f"  ⏭ HN元数据跳过: {title[:50]}")
                    continue
                save_prey("hn", title, text,
                          item.get("url", ""), item.get("score", 0))
                count += 1
    except Exception as e:
        print(f"  ⚠ HN 异常: {e}")
    return count


# ═══════════════════════════════════════════════════
# 猎场2: 掘金
# ═══════════════════════════════════════════════════

def hunt_juejin():
    count = 0
    try:
        payload = json.dumps({
            "key_word": "AI工具 大模型 ChatGPT",
            "cursor": "0", "limit": 20, "search_id": ""
        }).encode("utf-8")
        data = fetch_json("https://api.juejin.cn/search_api/v1/search", data=payload)
        existing = get_existing_titles("juejin")
        for item in data.get("data", []):
            info = item.get("article_info", {})
            title = (info.get("title", "") or "").strip()
            if not title or title in existing: continue
            abstract = info.get("brief_content", "") or info.get("brief", "") or ""
            article_url = f"https://juejin.cn/post/{info.get('article_id', '')}"
            if is_matched(title + abstract):
                save_prey("juejin", _u(title),
                          _u(abstract)[:200], article_url)
                count += 1
    except Exception as e:
        print(f"  ⚠ 掘金 异常: {e}")
    return count


# ═══════════════════════════════════════════════════
# 猎场3: GitHub Search
# ═══════════════════════════════════════════════════

def hunt_github():
    count = 0
    try:
        queries = ["AI+tool+LLM", "agent+framework", "machine+learning+tool", "openai+cli"]
        existing = get_existing_titles("github")
        gh_token = os.environ.get("GITHUB_TOKEN", "")
        for q in queries:
            try:
                url = f"https://api.github.com/search/repositories?q={q}&sort=stars&order=desc&per_page=5"
                headers = {
                    "User-Agent": "AIbounty/3.0",
                    "Accept": "application/vnd.github.v3+json"
                }
                if gh_token:
                    headers["Authorization"] = f"Bearer {gh_token}"
                req = urllib.request.Request(url, headers=headers)
                resp = json.loads(urllib.request.urlopen(req, timeout=10).read())
                for repo in resp.get("items", [])[:5]:
                    full_name = repo.get("full_name", "")
                    if full_name in existing: continue
                    desc = repo.get("description", "") or ""
                    stars = repo.get("stargazers_count", 0)
                    repo_url = repo.get("html_url", "")
                    save_prey("github", full_name, desc[:200], repo_url, stars)
                    count += 1
                    existing.add(full_name)
                time.sleep(2)  # 延缓防限
            except Exception as qe:
                print(f"  ⚠ GitHub query '{q}' 异常: {qe}")
                time.sleep(5)
    except Exception as e:
        print(f"  ⚠ GitHub 异常: {e}")
    return count


# ═══════════════════════════════════════════════════
# 猎场4: Product Hunt （差异化 — 每日新工具首发）
# ═══════════════════════════════════════════════════

def hunt_producthunt():
    """PH RSS feed — 比爬页面稳定，已确认国内可访问"""
    count = 0
    try:
        existing = get_existing_titles("producthunt")
        text = fetch_text("https://www.producthunt.com/feed?category=tech", timeout=15)
        # RSS XML 解析
        import xml.etree.ElementTree as ET
        root = ET.fromstring(text)
        ns = {"": "http://www.w3.org/2005/Atom"}
        entries = root.findall(".//entry", ns) if root.findall(".//entry", ns) else root.findall("entry")
        if not entries:
            # 可能是 RSS 2.0 格式
            entries = root.findall(".//item")
        for entry in entries[:25]:
            # 尝试多种标签名
            title_el = entry.find("title") or entry.find("{http://www.w3.org/2005/Atom}title")
            link_el = entry.find("link") or entry.find("{http://www.w3.org/2005/Atom}link")
            title = (title_el.text or "").strip() if title_el is not None else ""
            if not title or title in existing: continue
            # 提取链接
            href = ""
            if link_el is not None:
                href = link_el.get("href", "") or link_el.text or ""
            if is_matched(title):
                save_prey("producthunt", html.unescape(title), "", href)
                count += 1
                existing.add(title)
    except Exception as e:
        print(f"  ⚠ ProductHunt 异常: {e}")
    return count


# ═══════════════════════════════════════════════════
# 猎场5: V2EX （替代 Reddit — 国内可访问的技术社区）
# ═══════════════════════════════════════════════════
# 猎场5: OSChina 开源中国 （国内可访问 · AI项目讨论）
# ═══════════════════════════════════════════════════

def hunt_oschina():
    """OSChina — 国内开发者社区，有AI项目板块"""
    count = 0
    try:
        existing = get_existing_titles("oschina")
        page = fetch_text("https://www.oschina.net/news/project?sort=time", timeout=15)
        pattern = r'<a[^>]+href="(/news/[^"]+)"[^>]*>([^<]+)</a>'
        matches = re.findall(pattern, page)
        seen = set()
        for href, title in matches[:30]:
            title = _u(re.sub(r'<[^>]+>', '', title.strip()))
            if not title or len(title) < 3: continue
            if title in existing or title in seen: continue
            full_url = f"https://www.oschina.net{href}" if href.startswith("/") else href
            if is_matched(title):
                save_prey("oschina", title, "", full_url)
                count += 1
                seen.add(title)
    except Exception as e:
        print(f"  ⚠ OSChina 异常: {e}")
    return count


# ═══════════════════════════════════════════════════
# 猎场6: 魔搭 ModelScope （替代 HuggingFace — 国内AI模型社区）
# ═══════════════════════════════════════════════════

def hunt_modelscope():
    """魔搭社区 ModelScope — 国内AI模型平台"""
    count = 0
    try:
        existing = get_existing_titles("modelscope")
        # 多个备选API
        apis = [
            "https://modelscope.cn/api/v1/models?PageSize=20&OrderBy=downloads&Target=public",
            "https://modelscope.cn/api/v1/models?PageSize=20&Sort=downloads",
            "https://modelscope.cn/api/v1/models?PageSize=20",
        ]
        models = []
        for api_url in apis:
            try:
                data = fetch_json(api_url, timeout=10)
                models = data.get("Data", []) or data.get("data", []) or []
                if models: break
            except: continue

        if not models:
            # 备用：爬热门页面
            try:
                page = fetch_text("https://modelscope.cn/models", timeout=10)
                titles = re.findall(r'<div[^>]*class="[^"]*model-name[^"]*"[^>]*>([^<]+)<', page)
                for t in titles[:20]:
                    t = t.strip()
                    if t and t not in existing and is_matched(t):
                        save_prey("modelscope", _u(t), "")
                        count += 1
                        existing.add(t)
            except: pass
            return count

        for m in models:
            name = m.get("Name", "") or m.get("name", "") or m.get("ModelName", "") or ""
            if not name or name in existing: continue
            desc = str(m.get("Description", "") or m.get("description", "") or "")
            downloads = int(m.get("Downloads", 0) or m.get("downloads", 0) or 0)
            score = downloads
            if is_matched(name + desc):
                save_prey("modelscope", name, desc[:200],
                          f"https://modelscope.cn/models/{name}", score)
                count += 1
                existing.add(name)
    except Exception as e:
        print(f"  ⚠ 魔搭 异常: {e}")
    return count


# ═══════════════════════════════════════════════════
# 猎场7: ArXiv （差异化 — 论文→工具的提前嗅探）
# ═══════════════════════════════════════════════════

def hunt_arxiv():
    """ArXiv 最新AI论文 — 提前发现还没变成产品的技术"""
    count = 0
    try:
        existing = get_existing_titles("arxiv")
        url = ("http://export.arxiv.org/api/query?"
               "search_query=cat:cs.AI+AND+cat:cs.LG&"
               "sortBy=submittedDate&sortOrder=descending&max_results=20")
        xml_text = fetch_text(url)
        root = ElementTree.fromstring(xml_text)

        ns = {"a": "http://www.w3.org/2005/Atom",
              "arxiv": "http://arxiv.org/schemas/atom"}
        for entry in root.findall("a:entry", ns):
            title = entry.find("a:title", ns)
            summary = entry.find("a:summary", ns)
            link = entry.find("a:id", ns)
            title_text = (title.text or "").replace("\n", " ").strip() if title is not None else ""
            if not title_text or title_text in existing: continue
            summary_text = (summary.text or "").replace("\n", " ").strip()[:200] if summary is not None else ""
            link_url = (link.text or "").strip() if link is not None else ""

            # 只保留有实用潜力的论文（非纯理论）
            practical_kw = ["tool", "framework", "system", "benchmark", "dataset",
                           "application", "pipeline", "platform", "library",
                           "toolkit", "engine", "agent", "rag", "generation"]
            check = (title_text + summary_text).lower()
            if any(kw in check for kw in practical_kw) and is_matched(check):
                save_prey("arxiv", title_text[:120], summary_text, link_url)
                count += 1
                existing.add(title_text)
    except Exception as e:
        print(f"  ⚠ ArXiv 异常: {e}")
    return count


# ═══════════════════════════════════════════════════
# 猎场8: Gitee （差异化 — 国内开源，有信息差）
# ═══════════════════════════════════════════════════

def hunt_gitee():
    """Gitee 码云 — 使用搜索API + 探索页双通道"""
    count = 0
    try:
        existing = get_existing_titles("gitee")
        token = os.environ.get("GITEE_TOKEN", "")
        
        # 通道1: Gitee API v5 搜索（需要token但更稳定）
        if token:
            try:
                # 搜索AI相关项目
                search_urls = [
                    f"https://gitee.com/api/v5/search/repositories?q=AI&sort=stars_count&order=desc&page=1&per_page=20&access_token={token}",
                    f"https://gitee.com/api/v5/search/repositories?q=%E4%BA%BA%E5%B7%A5%E6%99%BA%E8%83%BD&sort=stars_count&page=1&per_page=20&access_token={token}",
                    f"https://gitee.com/api/v5/search/repositories?q=agent&sort=stars_count&page=1&per_page=20&access_token={token}",
                ]
                for surl in search_urls:
                    try:
                        data = fetch_json(surl, timeout=10)
                        repos = data.get("data", []) if isinstance(data, dict) else data
                        for repo in repos[:10]:
                            full_name = repo.get("full_name", "")
                            if not full_name or full_name in existing: continue
                            desc = repo.get("description", "") or ""
                            stars = repo.get("stargazers_count", 0)
                            if is_matched(full_name + desc):
                                save_prey("gitee", full_name, desc[:200],
                                          f"https://gitee.com/{full_name}", stars)
                                count += 1
                                existing.add(full_name)
                        if count >= 5: break
                    except: continue
            except Exception as e:
                print(f"  ↪ Gitee API 异常: {e}")
        
        # 通道2: 探索页抓取（无token时使用，较慢但可用）
        if count < 3:
            try:
                # 使用移动端页面减少反爬
                pages = [
                    "https://gitee.com/explore/ai",
                    "https://gitee.com/explore?q=AI&type=project",
                ]
                for page_url in pages:
                    try:
                        page = fetch_text(page_url, timeout=12)
                        # 匹配项目链接
                        project_pattern = r'https://gitee\.com/([^/"\'<>?]+/[^/"\'<>?]+)'
                        projects = list(set(re.findall(project_pattern, page)))
                        for full_name in projects[:20]:
                            if full_name in existing: continue
                            name = full_name.split("/")[-1]
                            if is_matched(name):
                                save_prey("gitee", full_name, "", f"https://gitee.com/{full_name}")
                                count += 1
                                existing.add(full_name)
                        if count >= 3: break
                    except: continue
            except Exception as e:
                print(f"  ↪ Gitee 探索页抓取异常: {e}")
                
    except Exception as e:
        print(f"  ⚠ Gitee 异常: {e}")
    return count


# ═══════════════════════════════════════════════════
# 猎场9: 思否 SegmentFault （国内技术社区 · AI话题）
# ═══════════════════════════════════════════════════

def hunt_sf():
    """SegmentFault 思否 — 国内技术问答社区，AI板块活跃"""
    count = 0
    try:
        existing = get_existing_titles("sf")
        # 思否头条 — AI 相关
        urls = [
            "https://segmentfault.com/t/%E4%BA%BA%E5%B7%A5%E6%99%BA%E8%83%BD/blogs",
            "https://segmentfault.com/t/ai/blogs",
        ]
        for url in urls:
            try:
                page = fetch_text(url, timeout=12)
                # 提取文章标题和链接
                title_pattern = r'<a[^>]+href="(/a/[^"]+)"[^>]*>([^<]+)</a>'
                matches = re.findall(title_pattern, page)
                for href, title in matches[:15]:
                    title = html.unescape(title.strip())
                    if not title or len(title) < 5 or title in existing: continue
                    if is_matched(title):
                        save_prey("sf", title, "", f"https://segmentfault.com{href}")
                        count += 1
                        existing.add(title)
                if count >= 3: break
            except: continue
    except Exception as e:
        print(f"  ⚠ 思否 异常: {e}")
    return count


# ═══════════════════════════════════════════════════
# 生成日报
# ═══════════════════════════════════════════════════

def generate_daily_report():
    today = time.strftime("%Y-%m-%d")
    prey_files = sorted(PREY_DIR.glob("tp-*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    all_prey = []
    for pf in prey_files:
        try:
            with open(pf, "r", encoding="utf-8") as f:
                all_prey.append(json.load(f))
        except: pass

    # 按来源分组
    by_source = {}
    for p in all_prey:
        src = p.get("source", "unknown")
        by_source.setdefault(src, []).append(p)

    src_labels = {
        "hn": "HackerNews", "juejin": "掘金", "github": "GitHub",
        "producthunt": "Product Hunt", "oschina": "OSChina",
        "modelscope": "魔搭", "arxiv": "ArXiv", "gitee": "Gitee"
    }

    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><title>AIbounty · 每日AI工具简报</title>
<style>
body {{font-family:-apple-system,'Segoe UI',sans-serif;max-width:800px;margin:0 auto;padding:20px;background:#f8f9fa;color:#333;}}
h1 {{color:#2563eb;border-bottom:2px solid #2563eb;padding-bottom:8px;}}
h2 {{color:#374151;margin-top:24px;font-size:16px;}}
.date {{color:#6b7280;font-size:14px;}}
.item {{background:#fff;padding:10px 14px;margin:6px 0;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.08);}}
.item h3 {{margin:0 0 3px;font-size:14px;}}
.item h3 a {{color:#2563eb;text-decoration:none;}}
.item p {{margin:3px 0;font-size:13px;color:#6b7280;}}
.item .meta {{font-size:11px;color:#9ca3af;}}
.tag {{display:inline-block;padding:1px 6px;border-radius:4px;font-size:11px;color:#fff;margin-right:4px;}}
.tag-hn {{background:#ff6b35;}}
.tag-github {{background:#24292e;}}
.tag-juejin {{background:#1e80ff;}}
.tag-producthunt {{background:#da552f;}}
.tag-reddit {{background:#ff4500;}}
.tag-huggingface {{background:#f9d546;color:#333;}}
.tag-arxiv {{background:#b31b1b;}}
.tag-gitee {{background:#c71d23;}}
</style></head>
<body>
<h1>🏴‍☠️ AIbounty · 每日AI工具简报</h1>
<p class="date">📅 {today} · 共 {len(all_prey)} 条 · 覆盖 {len(by_source)} 个猎场</p>
<p class="date">📊 各源统计: {', '.join(f'{src_labels.get(s,s)}: {len(v)}' for s,v in sorted(by_source.items()))}</p>
"""

    # 各来源区块
    for src in ["github", "producthunt", "hn", "oschina", "modelscope", "arxiv", "juejin", "gitee"]:
        items = by_source.get(src, [])[:8]
        if not items: continue
        label = src_labels.get(src, src)
        tag_class = f"tag-{src}"
        html_content += f'<h2>{label}</h2>\n'
        for p in items:
            score_str = ""
            if p.get("score"):
                s = int(p["score"])
                if s > 1000000: score_str = f"🔥 {s//1000}k"
                elif s > 1000: score_str = f"⭐ {s//1000}.{str(s)[-3] or ''}k"
                else: score_str = f"⭐ {s}"
            html_content += (
                f'<div class="item">'
                f'<span class="tag {tag_class}">{label}</span>'
                f'<h3><a href="{p["url"]}" target="_blank">{p["title"][:60]}</a></h3>'
                f'<p>{p["abstract"][:80]}</p>'
                f'<div class="meta">{score_str} · {p.get("captured_at","")[:10]}</div>'
                f'</div>\n')

    html_content += "</body></html>"
    report_path = REPORT_DIR / f"daily-{today}.html"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"\n📄 日报已生成: {report_path}")
    return report_path


# ═══════════════════════════════════════════════════
# 入口
# ═══════════════════════════════════════════════════

if __name__ == "__main__":
    print("🏴‍☠️ AIbounty 狩猎引擎 v3 · 8源并行")
    print("=" * 42)
    start = time.time()

    # 定义猎场清单（名称，函数，描述）
    grounds = [
        ("hn",           hunt_hn,           "HackerNews"),
        ("github",       hunt_github,       "GitHub"),
        ("producthunt",  hunt_producthunt,  "Product Hunt"),
        ("gitee",        hunt_gitee,        "Gitee 码云"),
        ("sf",           hunt_sf,           "思否 SegmentFault"),
        ("oschina",      hunt_oschina,      "OSChina"),
        ("modelscope",   hunt_modelscope,   "魔搭 ModelScope"),
        ("arxiv",        hunt_arxiv,        "ArXiv"),
        ("juejin",       hunt_juejin,       "掘金"),
    ]

    results = {}
    for key, func, label in grounds:
        print(f"\n🔍 {label}...")
        try:
            n = func()
            results[key] = n
            print(f"  → {n} 条")
        except Exception as e:
            print(f"  ❌ 失败: {e}")
            results[key] = 0

    elapsed = time.time() - start
    total = sum(results.values())

    print("\n" + "=" * 42)
    print(f"📊 狩猎完成 · 耗时 {elapsed:.0f}s")
    for key, label in [(k, v) for k, v in [("github","GitHub"), ("producthunt","ProductHunt"),
                       ("oschina","OSChina"), ("modelscope","魔搭"), ("arxiv","ArXiv"),
                       ("gitee","Gitee"), ("hn","HN"), ("juejin","掘金")]]:
        print(f"   {label}: {results.get(key, 0)} 条")
    print(f"   ─────────────────")
    print(f"   总计: {total} 条")

    if total > 0:
        report = generate_daily_report()
        print(f"📄 日报: {report}")

    # 导出前端数据
    print("\n📊 导出前端数据...")
    import subprocess, sys
    export_script = BASE / "sop" / "export_data.py"
    if export_script.exists():
        r = subprocess.run([sys.executable, str(export_script)], capture_output=True, text=True)
        for line in r.stdout.strip().split("\n"):
            if line.strip():
                print(f"   {line.strip()}")

    # 数据质量检查
    qa_script = BASE / "sop" / "qa_check.py"
    if qa_script.exists():
        print("\n🔍 数据质量检查...")
        r = subprocess.run([sys.executable, str(qa_script)], capture_output=True, text=True)
        for line in r.stdout.strip().split("\n"):
            if line.strip():
                print(f"   {line.strip()}")
        if r.returncode != 0 and any("error" in l.lower() for l in r.stdout.split("\n")):
            print("   ⚠️ 发现质量问题，请查看 QA 报告")

    # 预上线检查（内部消化矛盾）
    preflight_script = BASE / "quality" / "preflight.py"
    if preflight_script.exists():
        print("\n🧪 预上线检查（矛盾内部消化）...")
        r = subprocess.run([sys.executable, str(preflight_script)], capture_output=True, text=True)
        for line in r.stdout.strip().split("\n"):
            if line.strip():
                print(f"   {line.strip()}")
        if r.returncode != 0:
            print("\n   ⚠️ 预检查未通过！修复以下问题后再上线：")
            # 提取失败项
            for line in r.stdout.split("\n"):
                if "❌" in line:
                    print(f"     {line.strip()}")

    # 生成内容素材包
    content_script = BASE / "sop" / "content_factory.py"
    if content_script.exists():
        print("\n📦 生成内容素材包...")
        r = subprocess.run([sys.executable, str(content_script)], capture_output=True, text=True)
        for line in r.stdout.strip().split("\n"):
            if line.strip():
                print(f"   {line.strip()}")

    # 生成 XCRN 全息仪表盘
    dash_script = BASE / "sop" / "generate_dashboard.py"
    if dash_script.exists():
        print("\n✦ 更新曦和仪表盘...")
        r = subprocess.run([sys.executable, str(dash_script)], capture_output=True, text=True)
        for line in r.stdout.strip().split("\n"):
            if line.strip():
                print(f"   {line.strip()}")

    print(f"\n✅ AIbounty v3 狩猎完成 · 8源 · {total} 条猎物")
