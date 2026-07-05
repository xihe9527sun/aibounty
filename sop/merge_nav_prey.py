#!/usr/bin/env python3
"""合并导航站猎物到data.json — 从prey目录批量导入新工具"""
import json, os, sys, re

PREY_DIR = r'E:\ToolPilot\prey'
DATA_JSON = r'E:\ToolPilot\data.json'

def load_data_json():
    """加载现有data.json"""
    if not os.path.exists(DATA_JSON):
        return []
    with open(DATA_JSON, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_nav_prey():
    """加载所有导航站猎物"""
    items = []
    for fname in os.listdir(PREY_DIR):
        if not fname.startswith('tp-nav-') or not fname.endswith('.json'):
            continue
        fpath = os.path.join(PREY_DIR, fname)
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            name = (data.get('name') or '').strip()
            if not name:
                continue
            items.append({
                'name': name,
                'url': data.get('url', ''),
                'description': data.get('description', ''),
                'source': data.get('source', 'nav_hunter'),
            })
        except:
            pass
    return items

def dedup_and_convert(new_items, existing_items):
    """去重并转换为data.json格式"""
    existing_names = set()
    for item in existing_items:
        name = (item.get('name') or '').strip().lower()
        if name:
            existing_names.add(name)
    
    converted = []
    seen_names = set()
    
    for item in new_items:
        name_lower = item['name'].lower().strip()
        if name_lower in existing_names or name_lower in seen_names:
            continue
        seen_names.add(name_lower)
        
        # 生成slug
        slug = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fff-]', '-', item['name'])
        slug = re.sub(r'-+', '-', slug).strip('-').lower()[:50]
        
        # 推断分类（从URL或描述）
        url = item.get('url', '')
        desc = item.get('description', '')
        
        new_entry = {
            'name': item['name'],
            'slug': slug,
            'url': url,
            'description': desc,
            'tags': [],
            'source': item.get('source', 'nav_hunter'),
            'category': '',
            'isFavorite': False,
            'addedAt': ''
        }
        converted.append(new_entry)
    
    return converted

# 加载
print('  📂 加载现有 data.json...')
existing = load_data_json()
print(f'    已有 {len(existing)} 个工具')

print('  📂 扫描导航站猎物...')
nav_items = load_nav_prey()
print(f'    发现 {len(nav_items)} 个猎物文件')

print('  🔄 去重转换...')
new_entries = dedup_and_convert(nav_items, existing)

print(f'  🆕 新增 {len(new_entries)} 个工具（已有{len(existing)}个）')
print(f'  📊 合并后总计: {len(existing) + len(new_entries)} 个')

if new_entries:
    # 合并
    all_tools = existing + new_entries
    with open(DATA_JSON, 'w', encoding='utf-8') as f:
        json.dump(all_tools, f, ensure_ascii=False, indent=2)
    print(f'  ✅ 已写入 {DATA_JSON}')
    
    # 预览
    print(f'\n  预览（前10个新增）:')
    for item in new_entries[:10]:
        print(f'    ✅ {item["name"]} — {item["description"][:40]}')
    if len(new_entries) > 10:
        print(f'    ... 还有 {len(new_entries)-10} 个')
    
    # 可以删除prey文件来清理
    print(f'\n  💡 确认无误后，可运行以下命令清理prey目录的导航站猎物:')
    print(f'     del /q E:\\ToolPilot\\prey\\tp-nav-*.json')
else:
    print('  ℹ️  没有新工具需要合并')
