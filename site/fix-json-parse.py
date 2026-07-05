#!/usr/bin/env python3
"""修复 data_tags 和 category 字段的 JSON 字符串解析问题"""
import re

with open('E:/ToolPilot/site/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

changes = []

# === Fix 1: category in card template (line ~2503) ===
# Replace: ${(item.category||[]).length?...item.category.map(...)...}
old_cat_card = r'item\.category\|\|\[\]'
pattern1 = re.compile(r'\$?\{\(item\.category\|\|\[\]\)\.length\?`<div class="cat-tags">\$?\{item\.category\.map\(c=>')
m1 = pattern1.search(html)
if m1:
    html = html.replace(
        m1.group(0),
        r'${(function(){var _c=item.category;if(typeof _c==="string"){try{_c=JSON.parse(_c)}catch(e){_c=[]}}return _c.length?`<div class="cat-tags">${_c.map(c=>'
    )
    changes.append('Fix 1: category card template')

# === Fix 2: category in hot category count (line ~2628) ===
old_cat_count = r"for (const c of item.category||[])"
if old_cat_count in html:
    html = html.replace(
        old_cat_count,
        r"for (const c of (function(){var _c=item.category;if(typeof _c==='string'){try{_c=JSON.parse(_c)}catch(e){_c=[]}}return _c||[]})())"
    )
    changes.append('Fix 2: category count')

# === Fix 3: category.some in search (line ~2898) ===
old_cat_some = r"(item.category && item.category.some(c => c.includes(q)))"
new_cat_some = r"((function(){var _c=item.category;if(typeof _c==='string'){try{_c=JSON.parse(_c)}catch(e){_c=[]}}return _c})()&&(function(){var _c=item.category;if(typeof _c==='string'){try{_c=JSON.parse(_c)}catch(e){_c=[]}}return _c})().some(c => c.includes(q)))"
if old_cat_some in html:
    # That's too long, let me be smarter - use a function wrapper
    html = html.replace(
        old_cat_some,
        r"((item._catCache||(item._catCache=(function(){var _c=item.category;if(typeof _c==='string'){try{_c=JSON.parse(_c)}catch(e){_c=[]}}return _c})()))&&item._catCache.some(c => c.includes(q)))"
    )
    changes.append('Fix 3: category.some search')

# === Fix 4: category slice in auto-complete (line ~2909) ===
old_cat_slice = r"(item.category||[]).slice(0,2).map(c => ({agent:'🤖',llm:'🧠',rag:'🔗','dev-tool':'🛠',media:'🎨','data-science':'📊'}[c]||'')).join(' ')"
new_cat_slice = r"(item._catCache||(item._catCache=(function(){var _c=item.category;if(typeof _c==='string'){try{_c=JSON.parse(_c)}catch(e){_c=[]}}return _c})())).slice(0,2).map(c => ({agent:'🤖',llm:'🧠',rag:'🔗','dev-tool':'🛠',media:'🎨','data-science':'📊'}[c]||'')).join(' ')"
if old_cat_slice in html:
    html = html.replace(old_cat_slice, new_cat_slice)
    changes.append('Fix 4: category slice auto-complete')

# === Fix 5: category.some in search match (line ~3036) ===
old_cat_some2 = r"(item.category||[]).some(c => c.toLowerCase().includes(q))"
new_cat_some2 = r"(item._catCache||(item._catCache=(function(){var _c=item.category;if(typeof _c==='string'){try{_c=JSON.parse(_c)}catch(e){_c=[]}}return _c})())).some(c => c.toLowerCase().includes(q))"
if old_cat_some2 in html:
    html = html.replace(old_cat_some2, new_cat_some2)
    changes.append('Fix 5: category.some match')

with open('E:/ToolPilot/site/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f'Fixed {len(changes)} issues:')
for c in changes:
    print(f'  {c}')
