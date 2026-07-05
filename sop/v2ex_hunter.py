#!/usr/bin/env python3
"""V2EX 狩猎脚本 — 被 hunt_v2ex.bat 调用"""
import urllib.request, json, os, time, sys

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
PREY_DIR = r'E:\ToolPilot\prey'

# AI 关键词
AI_KW = ['ai', 'gpt', 'llm', 'agent', 'chatgpt', 'claude', 'copilot',
         '大模型', '人工智能', 'chatbot', 'rag', 'openai', 'embedding',
         'neural', 'machine learning', '深度学习', 'transformer',
         'vision', '自动化', '智能', 'dataset', 'framework', 'model',
         'generation', 'pipeline', 'api', 'sdk', 'toolkit']

print('  连接 V2EX API...')
sys.stdout.flush()

try:
    req = urllib.request.Request('https://www.v2ex.com/api/topics/latest.json', headers=headers)
    resp = urllib.request.urlopen(req, timeout=30)
    topics = json.loads(resp.read())
    print(f'  ✅ 获取到 {len(topics)} 个最新话题')
    sys.stdout.flush()
except Exception as e:
    print(f'  ❌ API请求失败: {e}')
    # 备用：尝试热门话题
    try:
        print('  ↪ 尝试热门话题API...')
        req = urllib.request.Request('https://www.v2ex.com/api/topics/hot.json', headers=headers)
        resp = urllib.request.urlopen(req, timeout=30)
        topics = json.loads(resp.read())
        print(f'  ✅ 热门话题: {len(topics)} 条')
    except:
        print('  ❌ 全部失败，请检查网络')
        sys.exit(1)

count = 0
for t in topics[:40]:
    title = t.get('title', '').strip()
    if not title: continue
    # 关键词匹配
    title_lower = title.lower()
    kw_hit = [kw for kw in AI_KW if kw in title_lower]
    if not kw_hit: continue
    
    tid = t.get('id', '')
    url = t.get('url', '') or f'https://www.v2ex.com/t/{tid}'
    node = t.get('node', {}).get('title', '')
    
    fname = f'tp-v2ex-{int(time.time()*1000)}-{os.urandom(2).hex()}.json'
    data = {
        'source': 'v2ex', 'title': title[:120], 'abstract': '',
        'url': url, 'score': 0,
        'captured_at': time.strftime('%Y-%m-%d %H:%M:%S')
    }
    with open(os.path.join(PREY_DIR, fname), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    kw_str = ', '.join(kw_hit[:3])
    node_str = f' [{node}]' if node else ''
    print(f'  ✅ {title[:55]}  ({kw_str}){node_str}')
    count += 1
    sys.stdout.flush()

if count == 0:
    print('\n  ℹ️  未发现AI相关话题')
    print('  最近话题（供参考）:')
    for t in topics[:5]:
        print(f'    - {t.get("title","?")[:45]}')
else:
    print(f'\n  🎯 共捕获 {count} 条猎物')

print(f'\n  结果已保存至: {PREY_DIR}')
