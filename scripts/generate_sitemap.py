#!/usr/bin/env python3
"""Generate sitemap.xml for aibounty.cn
Includes: tool pages, static pages, daily pages, RSS/Atom feeds
Usage: python scripts/generate_sitemap.py
"""
import json, os, glob

SITE_DIR = os.path.join(os.path.dirname(__file__), '..', 'site')
DATA_JSON = os.path.join(SITE_DIR, 'data.json')
SITEMAP = os.path.join(SITE_DIR, 'sitemap.xml')
DAILY_DIR = os.path.join(SITE_DIR, 'daily')

with open(DATA_JSON, 'r', encoding='utf-8') as f:
    data = json.load(f)
items = data.get('items', [])

BASE = 'https://www.aibounty.cn'
lines = [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    f'  <url><loc>{BASE}/</loc><changefreq>daily</changefreq><priority>1.0</priority></url>',
]

# Tool pages
for it in items:
    tid = it.get('id', '')
    if tid:
        lines.append(f'  <url><loc>{BASE}/tool.html?id={tid}</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>')

# Static pages
CAT_PAGES = ['agent.html', 'llm.html', 'dev-tool.html', 'rag.html', 'media.html', 'data-science.html', 'uncategorized.html']
static_pages = [('about.html', '0.5'), ('daily.html', '0.6')] + [(p, '0.7') for p in CAT_PAGES]
for page, pri in static_pages:
    lines.append(f'  <url><loc>{BASE}/{page}</loc><changefreq>weekly</changefreq><priority>{pri}</priority></url>')

# Daily pages
daily_files = glob.glob(os.path.join(DAILY_DIR, '*.html'))
for df in daily_files:
    name = os.path.basename(df)
    lines.append(f'  <url><loc>{BASE}/daily/{name}</loc><changefreq>monthly</changefreq><priority>0.6</priority></url>')

# RSS/Atom feeds
for feed in ['feed.xml', 'atom.xml']:
    lines.append(f'  <url><loc>{BASE}/{feed}</loc><changefreq>daily</changefreq><priority>0.3</priority></url>')

lines.append('</urlset>')

with open(SITEMAP, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

url_count = len(items) + 1  # home
url_count += 2 + len(CAT_PAGES)  # about, daily, category pages
url_count += len(daily_files)
url_count += 2  # feeds
print(f'[OK] sitemap.xml: {len(lines)} lines, {url_count} URLs')
