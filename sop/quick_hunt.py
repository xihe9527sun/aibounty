#!/usr/bin/env python3
"""
AIbounty 快速狩猎脚本 · 仅狩猎可靠源
Simon Willison + The Verge AI + Product Hunt
带每个源的硬超时限制
"""
import urllib.request, json, os, time, re, html, socket, sys
from pathlib import Path
from xml.etree import ElementTree

BASE = Path("E:/ToolPilot")
PREY_DIR = BASE / "prey"
socket.setdefaulttimeout(15)  # 全局socket超时15秒

AI_KW = ["ai ", "gpt", "llm", "agent", "chatgpt", "claude", "copilot",
         "人工智能", "大模型", "AI工具", "深度学习", "机器学习",
         "openai", "anthropic", "mistral", "gemini", "deepseek",
         "transformer", "rag", "embedding", "vector", "neural",
         "ai agent", "ai tools", "chatbot", "vision",
         "producthunt", "startup", "saas", "自动化", "智能"]

def _u(text):
    try: return html.unescape(str(text))
    except: return str(text)

def save_prey(source, title, abstract="", url="", score=0):
    if not url or not url.startswith("http"): return 0
    if not abstract or len(abstract.strip()) < 5: return 0
    if len(title.strip()) < 8: return 0
    fname = f"tp-{source}-{int(time.time()*1000)}-{os.urandom(2).hex()}.json"
    data = {"source": source, "title": title.strip()[:120],
            "abstract": (abstract or "")[:300], "url": url, "score": score,
            "captured_at": time.strftime("%Y-%m-%d %H:%M:%S")}
    path = PREY_DIR / fname
    with open(str(path), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  ✅ {title[:50]}")
    return 1

def get_existing_titles(source):
    titles = set()
    for pf in PREY_DIR.glob(f"tp-{source}-*.json"):
        try:
            with open(pf, "r", encoding="utf-8") as f:
                titles.add(json.load(f).get("title", ""))
        except: pass
    return titles

def fetch_feed(url, timeout=15):
    """Fetch RSS/Atom feed text with timeout."""
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })
    return urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8", errors="replace")

def is_matched(text):
    if not text: return False
    t = text.lower()
    return any(kw in t for kw in AI_KW)

def parse_atom_entry(entry):
    """Parse an Atom entry and return (title, desc, link) or None."""
    title_el = entry.find("title") or entry.find("{http://www.w3.org/2005/Atom}title")
    if title_el is None or title_el.text is None:
        return None
    title = _u(title_el.text.strip())[:120]
    if not title:
        return None
    
    desc_el = entry.find("summary") or entry.find("{http://www.w3.org/2005/Atom}summary")
    if desc_el is None:
        desc_el = entry.find("content") or entry.find("{http://www.w3.org/2005/Atom}content")
    desc = (desc_el.text or "") if desc_el is not None else ""
    
    link_el = entry.find("link") or entry.find("{http://www.w3.org/2005/Atom}link")
    link = link_el.get("href", "") if link_el is not None else ""
    
    return title, desc[:200], link

# ── 计数 ──
before = len(list(PREY_DIR.glob("tp-*.json")))
rss_before = len(list(PREY_DIR.glob("tp-rss-*.json")))

print("🏴‍☠️ AIbounty 快速狩猎 · 3个可靠源")
print("=" * 38)
print(f"猎物基线: {before} 个文件 (rss: {rss_before})")
print()

# ── 1. Simon Willison ──
count1 = 0
existing = get_existing_titles("rss")
print("🔍 Simon Willison...")
try:
    text = fetch_feed("https://simonwillison.net/atom/everything/")
    root = ElementTree.fromstring(text)
    entries = root.findall(".//entry") or root.findall(".//{http://www.w3.org/2005/Atom}entry")
    for entry in entries[:8]:
        result = parse_atom_entry(entry)
        if result is None: continue
        title, desc, link = result
        if title in existing: continue
        if is_matched(title + desc):
            count1 += save_prey("rss", title, _u(desc), link, score=1)
            existing.add(title)
    print(f"  → {count1} 条")
except Exception as e:
    print(f"  ⚠ {e}")

# ── 2. The Verge AI ──
count2 = 0
print("\n🔍 The Verge AI...")
try:
    text = fetch_feed("https://www.theverge.com/rss/ai-artificial-intelligence/index.xml")
    root = ElementTree.fromstring(text)
    entries = root.findall(".//entry") or root.findall(".//{http://www.w3.org/2005/Atom}entry")
    for entry in entries[:8]:
        result = parse_atom_entry(entry)
        if result is None: continue
        title, desc, link = result
        if title in existing: continue
        if is_matched(title + desc):
            count2 += save_prey("rss", title, _u(desc), link, score=1)
            existing.add(title)
    print(f"  → {count2} 条")
except Exception as e:
    print(f"  ⚠ {e}")

# ── 3. Product Hunt Tech ──
count3 = 0
print("\n🔍 Product Hunt Tech...")
try:
    text = fetch_feed("https://www.producthunt.com/feed?category=tech")
    root = ElementTree.fromstring(text)
    entries = root.findall(".//item")
    for entry in entries[:8]:
        title = entry.findtext("title", "") or ""
        if not title or title in existing: continue
        desc = entry.findtext("description", "") or ""
        link = entry.findtext("link", "") or ""
        if is_matched(title + desc):
            count3 += save_prey("rss", _u(title.strip())[:120], _u(desc[:200]), link, score=1)
            existing.add(title)
    print(f"  → {count3} 条")
except Exception as e:
    print(f"  ⚠ {e}")

# ── 统计 ──
after = len(list(PREY_DIR.glob("tp-*.json")))
rss_after = len(list(PREY_DIR.glob("tp-rss-*.json")))
elapsed = time.time() - t0 if 't0' in dir() else 0

print(f"\n{'='*38}")
print(f"✅ 狩猎完成")
print(f"   耗时: {elapsed:.0f}s" if elapsed else "")
print(f"   prey: {before} → {after} (+{after-before})")
print(f"   RSS:  {rss_before} → {rss_after} (+{rss_after-rss_before})")
print(f"   新增: {count1+count2+count3} 条")

# 写入结果
with open(str(BASE / "hunt_result.json"), "w") as f:
    json.dump({
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "prey_before": before, "prey_after": after,
        "rss_before": rss_before, "rss_after": rss_after,
        "simon": count1, "theverge": count2, "producthunt": count3,
        "total_new": count1+count2+count3
    }, f, indent=2)
