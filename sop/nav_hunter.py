#!/usr/bin/env python3
"""导航站狩猎脚本 v4 — 从AI工具集(ai-bot.cn)批量猎取精品工具
v4修复：工具卡片的属性顺序不一(href可能在前，class可能在后)
"""
import urllib.request, json, os, time, sys, re

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
PREY_DIR = r'E:\ToolPilot\prey'
DATA_JSON = r'E:\ToolPilot\data.json'

CATEGORIES = [
    ('ai-writing-tools', 'AI写作工具'),
    ('ai-image-tools', 'AI图像工具'),
    ('ai-video-tools', 'AI视频工具'),
    ('ai-office-tools', 'AI办公工具'),
    ('ai-agent', 'AI智能体'),
    ('ai-chatbots', 'AI聊天助手'),
    ('ai-programming-tools', 'AI编程工具'),
    ('ai-design-tools', 'AI设计工具'),
    ('ai-audio-tools', 'AI音频工具'),
    ('ai-search-engines', 'AI搜索引擎'),
    ('ai-frameworks', 'AI开发平台'),
    ('ai-content-detection-and-optimization-tools', 'AI内容检测'),
    ('ai-prompt-tools', 'AI提示指令'),
]

def load_existing():
    existing = set()
    if not os.path.exists(DATA_JSON):
        return existing
    try:
        with open(DATA_JSON, 'r', encoding='utf-8') as f:
            for item in json.load(f):
                name = (item.get('name') or '').strip()
                if name:
                    existing.add(name.lower())
    except:
        pass
    return existing

def extract_from_html(html_text):
    """从HTML提取工具卡片 - 属性顺序无关版本"""
    cards = []
    # 先找到所有 class 包含 site- 的链接（工具卡片）
    # 然后用更灵活的方式提取属性
    card_pattern = r'<a\s+[^>]*class=\"[^\"]*card[^\"]*site-\d+[^\"]*\"[^>]*>.*?</a>'
    
    for m in re.finditer(card_pattern, html_text, re.DOTALL | re.IGNORECASE):
        card_html = m.group()
        
        # 从卡片HTML中提取各属性
        href_m = re.search(r'href=\"([^\"]+)\"', card_html)
        title_m = re.search(r'title=\"([^\"]*)\"', card_html)
        name_m = re.search(r'<strong[^>]*>(.*?)</strong>', card_html, re.DOTALL)
        
        if not href_m or not name_m:
            continue
        
        href = href_m.group(1)
        title = title_m.group(1).strip() if title_m else ''
        name = re.sub(r'<[^>]+>', '', name_m.group(1)).strip()
        name = re.sub(r'\s+', ' ', name).strip()
        
        if not name or len(name) > 80:
            continue
        
        cards.append({
            'name': name,
            'url': href,
            'description': title
        })
    
    return cards

print('  🎯 导航站狩猎 · AI工具集 (ai-bot.cn)')
print(f'  📊 分类页数: {len(CATEGORIES)}')
sys.stdout.flush()

existing = load_existing()
print(f'  📊 data.json 已有 {len(existing)} 个工具')
sys.stdout.flush()

all_new = []
for slug, cat_name in CATEGORIES:
    url = f'https://www.ai-bot.cn/favorites/{slug}/'
    print(f'\n  📡 [{cat_name}]', end=' ', flush=True)
    
    try:
        req = urllib.request.Request(url, headers=headers)
        resp = urllib.request.urlopen(req, timeout=30)
        html = resp.read().decode('utf-8', errors='replace')
        cards = extract_from_html(html)
        
        new_cards = [c for c in cards if c['name'].lower() not in existing]
        if new_cards:
            all_new.extend(new_cards)
            for c in new_cards:
                existing.add(c['name'].lower())
        
        print(f'{len(cards)}个工具 → 🆕 {len(new_cards)}', flush=True)
        time.sleep(0.3)
        
    except Exception as e:
        print(f'❌ {str(e)[:50]}', flush=True)

print(f'\n  📦 共 {len(all_new)} 个新工具，保存中...', flush=True)

count = 0
for c in all_new:
    fname = f'tp-nav-{int(time.time()*1000)}-{os.urandom(2).hex()}.json'
    data = {
        'source': 'nav_hunter',
        'name': c['name'],
        'url': c['url'],
        'description': c['description'],
        'captured_at': time.strftime('%Y-%m-%d %H:%M:%S')
    }
    with open(os.path.join(PREY_DIR, fname), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    count += 1

print(f'\n  🎯 共保存 {count} 个新工具到 prey/')
print(f'  结果: {PREY_DIR}')
