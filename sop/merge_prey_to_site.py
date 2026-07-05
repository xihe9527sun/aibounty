#!/usr/bin/env python3
"""合并导航站猎物到AIbounty网站 data.json"""
import json, os, re, time

SITE_DATA = r'E:\ToolPilot\site\data.json'
PREY_DIR = r'E:\ToolPilot\prey'

def load_site_data():
    with open(SITE_DATA, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_nav_prey():
    items = []
    for fname in os.listdir(PREY_DIR):
        if not fname.startswith('tp-nav-') or not fname.endswith('.json'):
            continue
        try:
            with open(os.path.join(PREY_DIR, fname), 'r', encoding='utf-8') as f:
                data = json.load(f)
            name = (data.get('name') or '').strip()
            if name:
                items.append(data)
        except:
            pass
    return items

def make_slug(name):
    slug = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fff-]', '-', name)
    return re.sub(r'-+', '-', slug).strip('-').lower()[:60]

site = load_site_data()
existing_items = site.get('items', [])
existing_names = set(i.get('name', '').strip().lower() for i in existing_items if i.get('name'))

nav_items = load_nav_prey()

new_count = 0
added_names = set()
for item in nav_items:
    name = item['name'].strip()
    name_lower = name.lower()
    if name_lower in existing_names or name_lower in added_names:
        continue
    
    new_item = {
        'name': name,
        'slug': make_slug(name),
        'description': item.get('description', '')[:200],
        'url': item.get('url', ''),
        'tags': [],
        'source': 'nav_hunter',
        'category': '',
        'isFavorite': False,
        'addedAt': time.strftime('%Y-%m-%d')
    }
    existing_items.append(new_item)
    added_names.add(name_lower)
    new_count += 1

site['items'] = existing_items
site['total'] = len(existing_items)

with open(SITE_DATA, 'w', encoding='utf-8') as f:
    json.dump(site, f, ensure_ascii=False, indent=2)

print(f'  📊 原有: {len(existing_items) - new_count} 个工具')
print(f'  🆕 新增: {new_count} 个')
print(f'  📈 总计: {len(existing_items)} 个')
print(f'  ✅ 已更新: {SITE_DATA}')

if new_count > 0:
    print(f'\n  预览:')
    for item in existing_items[-min(10, new_count):]:
        print(f'    ✅ {item["name"]} — {item["description"][:40]}')
