#!/usr/bin/env python3
"""少数派狩猎脚本 — 被 hunt_sspai.bat 调用"""
import urllib.request, json, os, time, sys

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
PREY_DIR = r'E:\ToolPilot\prey'

AI_KW = ['ai','gpt','llm','agent','chatgpt','claude','大模型','人工智能',
         'chatbot','rag','openai','embedding','机器学习','深度学习',
         'neural','transformer','自动化','智能','vision','generation']

apis = [
    'https://sspai.com/api/v1/article/hot/page/get?limit=30',
    'https://sspai.com/api/v1/article/index/page/get?limit=30',
]

articles = []
for api in apis:
    try:
        print(f'  尝试API: {api.split("?")[0].split("/")[-1]}...')
        sys.stdout.flush()
        req = urllib.request.Request(api, headers=headers)
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read())
        items = data.get('data', []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
        if items:
            articles = items
            print(f'  ✅ 成功: {len(items)} 篇')
            sys.stdout.flush()
            break
    except Exception as e:
        print(f'  ⚠ 失败: {str(e)[:40]}')
        sys.stdout.flush()

if not articles:
    print('  ❌ 所有API均失败')
    sys.exit(1)

count = 0
for a in articles[:30]:
    title = (a.get('title', '') or '').strip()
    if not title: continue
    # 关键词过滤
    title_lower = title.lower()
    kw_hit = [kw for kw in AI_KW if kw in title_lower]
    if not kw_hit: continue
    
    aid = str(a.get('id', '') or a.get('article_id', '') or '')
    if not aid: continue
    url = f'https://sspai.com/post/{aid}'
    summary = (a.get('summary', '') or '')[:200]
    
    fname = f'tp-sspai-{int(time.time()*1000)}-{os.urandom(2).hex()}.json'
    data = {
        'source': 'sspai', 'title': title[:120], 'abstract': summary,
        'url': url, 'score': 0,
        'captured_at': time.strftime('%Y-%m-%d %H:%M:%S')
    }
    with open(os.path.join(PREY_DIR, fname), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    kw_str = ', '.join(kw_hit[:3])
    print(f'  ✅ {title[:50]}  ({kw_str})')
    count += 1
    sys.stdout.flush()

if count == 0:
    print('\n  ℹ️  未发现AI相关文章')
else:
    print(f'\n  🎯 共捕获 {count} 条')

print(f'\n  结果已保存至: {PREY_DIR}')
