#!/usr/bin/env python3
"""
AIbounty 狩猎脚本 v4 · 10源并行 + 精品过滤
新增: V2EX · 少数派 · 即刻 · Twitter/Nitter
"""
import urllib.request, json, os, time, re, html, socket
from pathlib import Path
from xml.etree import ElementTree
from datetime import datetime
socket.setdefaulttimeout(20)  # 全局硬超时，防止某些请求无限挂起

BASE = Path("E:/ToolPilot")
PREY_DIR = BASE / "prey"
REPORT_DIR = BASE / "reports"
PREY_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

AI_KW = ["ai ", "gpt", "llm", "agent", "chatgpt", "claude", "copilot",
         "人工智能", "大模型", "AI工具", "深度学习", "机器学习",
         "openai", "anthropic", "mistral", "gemini", "deepseek",
         "transformer", "rag", "embedding", "vector", "neural",
         "ai agent", "ai tools", "llm", "chatbot", "vision",
         "producthunt", "startup", "saas", "自动化", "智能"]

def _u(text):
    try: return html.unescape(str(text))
    except: return str(text)

def save_prey(source, title, abstract="", url="", score=0):
    if not url or not url.startswith("http"):
        print(f"  ⛔ {source}: {title[:40]}… → 无有效链接"); return None
    if not abstract or len(abstract.strip()) < 5:
        print(f"  ⛔ {source}: {title[:40]}… → 无描述"); return None
    thresholds = {"github": 100, "hn": 5, "producthunt": 3}
    if int(score or 0) < thresholds.get(source, 1):
        print(f"  ⛔ {source}: {title[:40]}… → 分数{score}未达标"); return None
    if len(title.strip()) < 8:
        print(f"  ⛔ {source}: {title[:40]}… → 标题过短"); return None

    fname = f"tp-{source}-{int(time.time()*1000)}-{os.urandom(2).hex()}.json"
    data = {"source": source, "title": title.strip()[:120],
            "abstract": (abstract or "")[:300], "url": url, "score": score,
            "captured_at": time.strftime("%Y-%m-%d %H:%M:%S")}
    path = PREY_DIR / fname
    with open(str(path), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  ✅ {source}: {title[:50]}")
    return path

def fetch_json(url, timeout=60, data=None):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    if data: headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers)
    return json.loads(urllib.request.urlopen(req, timeout=timeout).read())

def fetch_text(url, timeout=60):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })
    return urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8", errors="replace")

def is_matched(text):
    if not text: return False
    t = text.lower()
    return any(kw in t for kw in AI_KW)

def get_existing_titles(source):
    titles = set()
    for pf in PREY_DIR.glob(f"tp-{source}-*.json"):
        try:
            with open(pf, "r", encoding="utf-8") as f:
                titles.add(json.load(f).get("title", ""))
        except: pass
    return titles

# ── 猎场1: V2EX ──
def hunt_v2ex():
    """V2EX 最新AI相关讨论 — 优先使用公开API"""
    count = 0
    try:
        existing = get_existing_titles("v2ex")
        # 通道1: V1公开API（无需Token）— 最新话题
        api_urls = [
            "https://www.v2ex.com/api/topics/latest.json",
            "https://www.v2ex.com/api/topics/hot.json",
        ]
        topics = []
        for api_url in api_urls:
            try:
                data = fetch_json(api_url, timeout=60)
                if isinstance(data, list) and len(data) > 0:
                    topics = data
                    print(f"  ✅ V2EX V1 API 成功: {api_url.split('/')[-1]}")
                    break
            except:
                continue
        
        # 通道2: 网页抓取（API失败时降级）
        if not topics:
            try:
                page = fetch_text("https://www.v2ex.com/go/ai", timeout=90)
                import re
                matches = re.findall(r'<a[^>]*href="/t/\d+"[^>]*>([^<]{6,})</a>', page)
                for title in matches:
                    topics.append({"title": title.strip()[:120], "url": ""})
                print(f"  ↪ 降级为网页抓取: {len(matches)} 个话题")
            except:
                print(f"  ⚠ 网页抓取也失败")

        seen = set()
        for t in topics[:20]:
            title = _u(t.get("title", "")).strip()
            if not title or title in existing or title in seen: continue
            topic_id = t.get("id", "")
            url = t.get("url", "") or t.get("URL", "") or t.get("url", "")
            if not url and topic_id:
                url = f"https://www.v2ex.com/t/{topic_id}"
            if url and is_matched(title):
                save_prey("v2ex", title, "", url)
                count += 1; seen.add(title)
            if count >= 10: break
    except Exception as e:
        print(f"  ⚠ V2EX 异常: {e}")
    return count

# ── 猎场2: 少数派 sspai ──
def hunt_sspai():
    """少数派AI相关文章"""
    count = 0
    try:
        existing = get_existing_titles("sspai")
        urls = [
            "https://sspai.com/api/v1/article/hot/page/get?limit=20",
            "https://sspai.com/api/v1/article/index/page/get?limit=20",
            "https://sspai.com/api/v1/article/tag/page/get?tag=AI&limit=20",
        ]
        articles = []
        for api_url in urls:
            try:
                data = fetch_json(api_url, timeout=30)
                if isinstance(data, dict):
                    items = data.get("data") or data.get("list") or []
                    if isinstance(items, list) and len(items) > 0:
                        articles = items; break
                    # 尝试嵌套结构
                    for v in data.values():
                        if isinstance(v, list) and len(v) > 0:
                            articles = v; break
                elif isinstance(data, list) and len(data) > 0:
                    articles = data; break
            except:
                continue

        for a in articles[:20]:
            title = _u((a.get("title") or "").strip())
            if not title or title in existing: continue
            abstract = (a.get("summary") or a.get("desc") or "")[:200]
            a_id = str(a.get("id") or a.get("article_id") or "")
            url = f"https://sspai.com/post/{a_id}" if a_id else ""
            if url and is_matched(title + abstract):
                save_prey("sspai", title, abstract, url)
                count += 1; existing.add(title)
    except Exception as e:
        print(f"  ⚠ 少数派 异常: {e}")
    return count

# ── 猎场3: 即刻 Jike ──
def hunt_jike():
    """即刻AI相关话题讨论"""
    count = 0
    try:
        existing = get_existing_titles("jike")
        # 即刻热门话题API
        headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*",
            "x-jike-device-id": "web"
        }
        # 用搜索接口找AI相关内容
        search_payload = json.dumps({
            "query": "AI",
            "limit": 20
        }).encode("utf-8")
        req = urllib.request.Request(
            "https://app.jike.ruguoapp.com/1.0/search",
            data=search_payload,
            headers={**headers, "Content-Type": "application/json"}
        )
        resp = json.loads(urllib.request.urlopen(req, timeout=15).read())
        for item in resp.get("data", []):
            content = item.get("content", "") or ""
            title = content[:60]
            if not title or title in existing: continue
            abstract = content[:200]
            link = item.get("link", "") or ""
            if is_matched(abstract):
                save_prey("jike", title, abstract, link or f"https://web.okjike.com/topic/AI")
                count += 1; existing.add(title)
    except Exception as e:
        print(f"  ⚠ 即刻 异常: {e}")
    return count

# ── 猎场4: Twitter/X via Nitter RSS ──
def hunt_twitter():
    """通过 Nitter RSS 追踪AI相关账号的最新推文"""
    count = 0
    try:
        existing = get_existing_titles("twitter")
        # Nitter 实例列表
        nitter_instances = [
            "https://nitter.net",
            "https://nitter.poast.org",
            "https://nitter.1d4.us",
            "https://nitter.kavin.rocks",
            "https://nitter.lv",  # 新增实例
        ]
        accounts = [
            "producthunt", "AIthat_dev", "OpenAI", "AnthropicAI",
            "huggingface", "AiBreakFast", "goodside", "TheAI_Journal"
        ]
        for instance in nitter_instances:
            if count >= 5: break
            for account in accounts:
                if count >= 5: break
                try:
                    rss_url = f"{instance}/{account}/rss"
                    text = fetch_text(rss_url, timeout=10)
                    root = ElementTree.fromstring(text)
                    entries = root.findall(".//entry") or root.findall(".//{http://www.w3.org/2005/Atom}entry")
                    for entry in entries[:3]:
                        title_el = entry.find("title") or entry.find("{http://www.w3.org/2005/Atom}title")
                        link_el = entry.find("link") or entry.find("{http://www.w3.org/2005/Atom}link")
                        if title_el is None: continue
                        title = _u((title_el.text or "").strip())[:120]
                        if not title or title in existing: continue
                        href = link_el.get("href", "") if link_el is not None else ""
                        if href and is_matched(title):
                            save_prey("twitter", title, "", href)
                            count += 1; existing.add(title)
                except:
                    continue
            if count > 0:
                print(f"  ✅ Nitter 实例可用: {instance}")
                break
    except Exception as e:
        print(f"  ⚠ Twitter 异常: {e}")
    return count

# ── 猎场5: 通用RSS扫描（10源并行）──
ATOM_NS = "http://www.w3.org/2005/Atom"

def hunt_rss():
    """扫描精品AI博客RSS，发现还没被关注的新工具"""
    count = 0
    try:
        existing = get_existing_titles("rss")
        feeds = [
            # 个人博客
            ("https://simonwillison.net/atom/everything/", "Simon Willison"),
            ("https://stability.ai/blog/rss/feed.xml", "Stability AI"),
            ("https://blog.langchain.dev/feed/", "LangChain"),
            ("https://huggingface.co/blog/feed.xml", "HuggingFace"),
            # 科技媒体
            ("https://feeds.feedburner.com/TechCrunch/", "TechCrunch AI"),
            ("https://www.theverge.com/rss/ai-artificial-intelligence/index.xml", "The Verge AI"),
            ("https://www.artificialintelligence-news.com/feed/", "AI News"),
            # 开发者社区
            ("https://medium.com/feed/tag/artificial-intelligence", "Medium AI"),
            ("https://news.ycombinator.com/rss", "HackerNews RSS"),
            # 精选工具
            ("https://www.producthunt.com/feed?category=tech", "Product Hunt Tech"),
            ("https://aibounty.cn/rss.xml", "AIbounty"),
        ]
        ElementTree.register_namespace("", ATOM_NS)
        for feed_url, label in feeds:
            try:
                text = fetch_text(feed_url, timeout=20)
                root = ElementTree.fromstring(text)
                # 尝试RSS 2.0 (item) 和 Atom (entry + 命名空间回退)
                entries = root.findall(".//item") or root.findall(".//entry") or root.findall(f".//{{{ATOM_NS}}}entry")
                for entry in entries[:8]:
                    # 处理 Atom 命名空间条目
                    is_atom = entry.tag.endswith("}entry") or (entry.tag == "entry" and root.tag.endswith("}feed"))
                    if is_atom:
                        title_el = entry.find(f"{{{ATOM_NS}}}title")
                        if title_el is None: title_el = entry.find("title")
                        title = (title_el.text or "") if title_el is not None else ""
                        desc_el = entry.find(f"{{{ATOM_NS}}}summary")
                        if desc_el is None: desc_el = entry.find("summary")
                        if desc_el is None: desc_el = entry.find(f"{{{ATOM_NS}}}content")
                        if desc_el is None: desc_el = entry.find("content")
                        desc = (desc_el.text or "") if desc_el is not None else ""
                        link_el = entry.find(f"{{{ATOM_NS}}}link")
                        if link_el is None: link_el = entry.find("link")
                        link = link_el.get("href", "") if link_el is not None else ""
                    else:
                        title = entry.findtext("title", "") or ""
                        desc = entry.findtext("description", "") or entry.findtext("summary", "") or ""
                        link = entry.findtext("link", "") or ""
                    title = _u(title.strip())[:120]
                    if not title or title in existing: continue
                    # HackerNews 过滤：跳过 Show HN / Ask HN 等非工具讨论帖
                    if "HackerNews" in label:
                        tl = title.lower()
                        if any(tl.startswith(p) for p in ('show hn:', 'ask hn:', 'tell hn:', 'launch hn:')):
                            print(f"  ⏭ HN讨论帖跳过: {title[:50]}")
                            continue
                        # 也检查 desc 中的垃圾模式
                        dl = desc.lower()
                        if 'hn discussion' in dl or 'ask hn' in dl:
                            if len(desc) < 30:
                                print(f"  ⏭ HN元数据跳过: {title[:50]}")
                                continue
                    if is_matched(title + desc):
                        save_prey("rss", title, _u(desc[:200]), link, score=1)
                        count += 1; existing.add(title)
                print(f"  ✅ {label}: 扫描完成")
            except Exception as e:
                print(f"  ⚠ {label}: {e}")
                continue
    except Exception as e:
        print(f"  ⚠ RSS 异常: {e}")
    return count

# ── 已有猎场（精简导入）──
def hunt_v2ex_simple(): return hunt_v2ex()

def hunt_jike_simple(): return hunt_jike()

def hunt_sspai_simple(): return hunt_sspai()

def hunt_twitter_simple(): return hunt_twitter()

def hunt_rss_simple(): return hunt_rss()

# ── 日报生成 ──
def generate_daily_report():
    today = time.strftime("%Y-%m-%d")
    prey_files = sorted(PREY_DIR.glob("tp-*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    all_prey = []
    for pf in prey_files:
        try:
            with open(pf, "r", encoding="utf-8") as f:
                all_prey.append(json.load(f))
        except: pass

    by_source = {}
    for p in all_prey:
        by_source.setdefault(p.get("source","unknown"), []).append(p)

    src_labels = {
        "hn": "HackerNews", "juejin": "掘金", "github": "GitHub",
        "producthunt": "Product Hunt", "v2ex": "V2EX",
        "sspai": "少数派", "jike": "即刻", "twitter": "Twitter/X",
        "rss": "RSS博客", "oschina": "OSChina",
        "modelscope": "魔搭", "arxiv": "ArXiv", "gitee": "Gitee"
    }

    print(f"\n📊 今日猎物统计:")
    for src, items in sorted(by_source.items()):
        print(f"   {src_labels.get(src,src)}: {len(items)} 条")
    print(f"   总计: {len(all_prey)} 条")
    return all_prey

if __name__ == "__main__":
    print("🏴‍☠️ AIbounty 狩猎引擎 v4 · 10源并行")
    print("=" * 42)
    start = time.time()

    grounds = [
        ("rss",        hunt_rss,         "RSS博客 (10源)"),
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
    print(f"\n✅ 新猎场狩猎完成 · 耗时 {elapsed:.0f}s · 新增 {total} 条")
    if total > 0:
        generate_daily_report()
    else:
        print("  本次无新增精品猎物")
