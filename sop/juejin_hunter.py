#!/usr/bin/env python3
"""掘金狩猎脚本 — 被 hunt_juejin.bat 调用"""
import urllib.request, json, os, time, sys

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
PREY_DIR = r'E:\ToolPilot\prey'

AI_CATEGORY_ID = '6809637773935378440'  # 人工智能分类

# AI关键词（文章标题匹配）
AI_KW = ['ai', 'gpt', 'llm', 'agent', 'chatgpt', 'claude', 'copilot',
         '大模型', '人工智能', 'chatbot', 'rag', 'openai', 'embedding',
         'neural', 'machine learning', '深度学习', 'transformer',
         'vision', '自动化', '智能', 'dataset', 'framework', 'model',
         'generation', 'pipeline', 'api', 'sdk', 'toolkit',
         'langchain', 'huggingface', 'stable diffusion', 'midjourney']

def check_title(title):
    """检查标题是否匹配AI关键词"""
    if not title:
        return []
    t = title.lower()
    return [kw for kw in AI_KW if kw in t]

def save_prey(source, title, url, abstract='', score=0):
    """保存一条猎物到prey目录"""
    fname = f'tp-{source}-{int(time.time()*1000)}-{os.urandom(2).hex()}.json'
    data = {
        'source': source,
        'title': title[:120],
        'abstract': (abstract or '')[:200],
        'url': url,
        'score': score,
        'captured_at': time.strftime('%Y-%m-%d %H:%M:%S')
    }
    with open(os.path.join(PREY_DIR, fname), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return fname

# ── 方式1：热榜 (GET, 无需参数) ──
print('  🔥 方式1：获取综合热榜...')
sys.stdout.flush()

total = 0
try:
    req = urllib.request.Request(
        'https://api.juejin.cn/content_api/v1/content/article_rank?category_id=1&type=hot',
        headers=headers
    )
    resp = urllib.request.urlopen(req, timeout=20)
    rank_data = json.loads(resp.read())
    articles = rank_data.get('data', [])
    print(f'  ✅ 热榜获取 {len(articles)} 条')
    
    for a in articles:
        info = a.get('content', {})
        title = info.get('title', '') or ''
        kw_hit = check_title(title)
        if not kw_hit:
            continue
        article_id = info.get('content_id', '') or info.get('article_id', '')
        url = f'https://juejin.cn/post/{article_id}'
        brief = (info.get('brief', '') or '')[:200]
        save_prey('juejin', title, url, brief)
        kw_str = ', '.join(kw_hit[:3])
        print(f'  ✅ [{kw_str}] {title[:50]}')
        total += 1
        sys.stdout.flush()
except Exception as e:
    print(f'  ℹ️ 热榜API: {e}')

# ── 方式2：AI分类推荐 (POST, 最新排序) ──
print(f'\n  📡 方式2：拉取AI分类最新文章...')
sys.stdout.flush()

try:
    body = json.dumps({
        "id_type": 2,
        "client_type": 2608,
        "sort_type": 300,  # 最新
        "cursor": "0",
        "limit": 30
    }).encode('utf-8')
    
    req2 = urllib.request.Request(
        f'https://api.juejin.cn/recommend_api/v1/article/recommend_all_feed?aid=2608',
        data=body,
        headers={**headers, 'Content-Type': 'application/json'}
    )
    resp2 = urllib.request.urlopen(req2, timeout=20)
    feed_data = json.loads(resp2.read())
    
    items = feed_data.get('data', [])
    ai_count = 0
    for item in items:
        if item.get('item_type') != 2:
            continue
        info = item.get('item_info', {})
        cat_id = info.get('category_id', '')
        title = info.get('article_info', {}).get('title', '') or ''
        
        # 如果分类ID是AI，直接捕获；否则关键词匹配
        if cat_id == AI_CATEGORY_ID:
            article_id = info.get('article_id', '')
            url = f'https://juejin.cn/post/{article_id}'
            brief = info.get('article_info', {}).get('brief_content', '')[:200]
            save_prey('juejin', title, url, brief, score=1)
            print(f'  ✅ [AI分类] {title[:50]}')
            total += 1
            ai_count += 1
            sys.stdout.flush()
            continue
        
        # 关键词匹配
        kw_hit = check_title(title)
        if kw_hit:
            article_id = info.get('article_id', '')
            url = f'https://juejin.cn/post/{article_id}'
            brief = info.get('article_info', {}).get('brief_content', '')[:200]
            save_prey('juejin', title, url, brief)
            kw_str = ', '.join(kw_hit[:3])
            print(f'  ✅ [{kw_str}] {title[:50]}')
            total += 1
            sys.stdout.flush()
    
    print(f'  ℹ️ 其中AI分类直接命中: {ai_count} 条')
except Exception as e:
    print(f'  ℹ️ 推荐API: {e}')

# ── 汇总 ──
if total == 0:
    print(f'\n  ℹ️  未发现AI相关文章')
else:
    print(f'\n  🎯 共捕获 {total} 条猎物')

print(f'\n  结果已保存至: {PREY_DIR}')
