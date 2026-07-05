#!/usr/bin/env python3
"""
generate_feed.py — aibounty RSS/Atom Feed 自动生成
==============================================
读取 data.json → 生成 RSS 2.0 + Atom 1.0 Feed
输出到 site/feed.xml 和 site/atom.xml

用法:
  python scripts/generate_feed.py
"""

import json, os
from datetime import datetime, timezone, timedelta

CST = timezone(timedelta(hours=8))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(ROOT, "site", "data.json")
FEED_FILE = os.path.join(ROOT, "site", "feed.xml")
ATOM_FILE = os.path.join(ROOT, "site", "atom.xml")

SITE_URL = "https://www.aibounty.cn"
FEED_DESC = "AIbounty - 每日狩猎全球最新 AI 工具。一站式发现 Agent、LLM、开发工具、RAG 框架等。"


def load_data():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def escape_xml(s):
    """安全转义 XML 特殊字符"""
    if not s:
        return ""
    s = str(s)
    s = s.replace("&", "&amp;")
    s = s.replace("<", "&lt;")
    s = s.replace(">", "&gt;")
    s = s.replace("\"", "&quot;")
    s = s.replace("'", "&apos;")
    return s


def gen_rss(items, updated_at_str):
    """生成 RSS 2.0 Feed"""
    now_str = datetime.now(CST).strftime("%a, %d %b %Y %H:%M:%S +0800")
    
    entries = ""
    for item in items[:50]:  # 最新 50 条
        title = escape_xml(item.get("title", "?"))
        desc = escape_xml(item.get("abstract_zh", "") or item.get("abstract", "") or "暂无描述")
        tid = item.get("id", "")
        url = f"{SITE_URL}/tool.html?id={tid}"
        score = item.get("score", 0) or 0
        cats = item.get("category", [])
        cat_str = " | ".join(cats) if cats else "AI"
        
        entries += f"""    <item>
      <title>{title}</title>
      <link>{url}</link>
      <description>{desc} (⭐ {score:,})</description>
      <category>{cat_str}</category>
      <guid isPermaLink="true">{url}</guid>
      <pubDate>{now_str}</pubDate>
    </item>
"""
    
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"
     xmlns:atom="http://www.w3.org/2005/Atom"
     xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <channel>
    <title>AIbounty - AI 工具日报</title>
    <link>{SITE_URL}</link>
    <description>{FEED_DESC}</description>
    <language>zh-CN</language>
    <lastBuildDate>{now_str}</lastBuildDate>
    <atom:link href="{SITE_URL}/feed.xml" rel="self" type="application/rss+xml"/>
    <image>
      <url>{SITE_URL}/favicon.ico</url>
      <title>AIbounty</title>
      <link>{SITE_URL}</link>
    </image>
{entries}  </channel>
</rss>
"""


def gen_atom(items):
    """生成 Atom 1.0 Feed"""
    now_iso = datetime.now(CST).strftime("%Y-%m-%dT%H:%M:%S+08:00")
    
    entries = ""
    for item in items[:50]:
        title = escape_xml(item.get("title", "?"))
        desc = escape_xml(item.get("abstract_zh", "") or item.get("abstract", "") or "暂无描述")
        tid = item.get("id", "")
        url = f"{SITE_URL}/tool.html?id={tid}"
        score = item.get("score", 0) or 0
        cats = item.get("category", [])
        cat_str = ", ".join(cats) if cats else "AI"
        
        entries += f"""  <entry>
    <id>{url}</id>
    <title>{title}</title>
    <link href="{url}" rel="alternate"/>
    <summary>{desc} (⭐ {score:,})</summary>
    <category term="{cat_str}"/>
    <updated>{now_iso}</updated>
  </entry>
"""
    
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xml:lang="zh-CN">
  <title>AIbounty - AI 工具日报</title>
  <subtitle>{FEED_DESC}</subtitle>
  <link href="{SITE_URL}" rel="alternate"/>
  <link href="{SITE_URL}/atom.xml" rel="self" type="application/atom+xml"/>
  <updated>{now_iso}</updated>
  <author>
    <name>AIbounty</name>
  </author>
  <icon>{SITE_URL}/favicon.ico</icon>
{entries}</feed>
"""


def main():
    data = load_data()
    items = data.get("items", [])
    total = len(items)
    
    # 按 score 排序，高星优先
    sorted_items = sorted(items, key=lambda x: x.get("score", 0) or 0, reverse=True)
    
    rss = gen_rss(sorted_items, data.get("updated_at", ""))
    with open(FEED_FILE, "w", encoding="utf-8") as f:
        f.write(rss)
    print(f"[OK] RSS Feed -> {FEED_FILE} (50条)")
    
    atom = gen_atom(sorted_items)
    with open(ATOM_FILE, "w", encoding="utf-8") as f:
        f.write(atom)
    print(f"[OK] Atom Feed -> {ATOM_FILE} (50条)")
    
    print(f"[OK] 数据源: {total} 个工具")


if __name__ == "__main__":
    main()
