#!/usr/bin/env python3
"""每日自动刷新脚本 — 掘金+少数派狩猎 → 合并 → 统计 → 推荐
被 daily_refresh.bat 调用，Windows计划任务触发
"""
import urllib.request, json, os, time, sys, re
from collections import Counter

# ── 配置 ──
PREY_DIR = r'E:\ToolPilot\prey'
SITE_DATA = r'E:\ToolPilot\site\data.json'
FLAG_FILE = r'C:\Users\Administrator\.workbuddy\deploy_pending.flag'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
AI_KW = ['ai','gpt','llm','agent','chatgpt','claude','copilot','大模型','人工智能','chatbot','rag','openai','embedding']

def log(msg):
    t = time.strftime('%H:%M:%S')
    print(f'  [{t}] {msg}')
    sys.stdout.flush()

def save_prey(source, title, url, desc=''):
    fn = f'tp-{source}-{int(time.time()*1000)}-{os.urandom(2).hex()}.json'
    d = {'source': source, 'name': title[:120], 'description': (desc or '')[:200],
         'url': url, 'captured_at': time.strftime('%Y-%m-%d %H:%M:%S')}
    with open(os.path.join(PREY_DIR, fn), 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

# ════════════════════════════════════════
# 第一步：掘金狩猎
# ════════════════════════════════════════
log('🏴‍☠️ 掘金狩猎...')
try:
    r = urllib.request.Request('https://api.juejin.cn/content_api/v1/content/article_rank?category_id=1&type=hot', headers=HEADERS)
    d = json.loads(urllib.request.urlopen(r, timeout=20).read())
    count = 0
    for a in (d.get('data') or []):
        info = a.get('content', {})
        title = (info.get('title') or '')
        if not any(kw in title.lower() for kw in AI_KW): continue
        aid = info.get('content_id','') or info.get('article_id','')
        save_prey('juejin', title, f'https://juejin.cn/post/{aid}', info.get('brief',''))
        count += 1
    log(f'  ✅ 掘金捕获 {count} 条')
except Exception as e:
    log(f'  ⚠️ 掘金: {e}')

# ════════════════════════════════════════
# 第二步：少数派狩猎
# ════════════════════════════════════════
log('🏴‍☠️ 少数派狩猎...')
try:
    apis = ['https://sspai.com/api/v1/article/hot/page/get?limit=30']
    for api in apis:
        r = urllib.request.Request(api, headers=HEADERS)
        resp = urllib.request.urlopen(r, timeout=15)
        data = json.loads(resp.read())
        items = data.get('data', []) if isinstance(data, dict) else []
        if items:
            count = 0
            for a in items:
                title = (a.get('title','') or '').strip()
                if not title or not any(kw in title.lower() for kw in AI_KW): continue
                aid = str(a.get('id','') or a.get('article_id','') or '')
                save_prey('sspai', title, f'https://sspai.com/post/{aid}', a.get('summary',''))
                count += 1
            log(f'  ✅ 少数派捕获 {count} 条')
            break
    else:
        log('  ⚠️ 少数派API无返回')
except Exception as e:
    log(f'  ⚠️ 少数派: {e}')

# ════════════════════════════════════════
# 第三步：合并到site/data.json
# ════════════════════════════════════════
log('📦 合并新工具...')
try:
    site = json.load(open(SITE_DATA, 'r', encoding='utf-8'))
    existing = site.get('items', [])
    # 兼容 title 和 name 两种字段
    existing_names = set()
    for i in existing:
        for k in ['title','name']:
            v = i.get(k,'')
            if v: existing_names.add(v.strip().lower())
    
    new_count = 0
    for fname in os.listdir(PREY_DIR):
        if not fname.endswith('.json'): continue
        if fname == 'data.json': continue
        try:
            prey = json.load(open(os.path.join(PREY_DIR, fname), 'r', encoding='utf-8'))
            name = (prey.get('name') or prey.get('title') or '').strip()
            if not name or name.lower() in existing_names: continue
            
            slug = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fff-]', '-', name)
            slug = re.sub(r'-+', '-', slug).strip('-').lower()[:60]
            
            item = {
                'title': name,
                'abstract': (prey.get('description') or '')[:200],
                'abstract_zh': (prey.get('description') or '')[:200],
                'url': prey.get('url', ''),
                'score': 1, 'id': slug,
                'source': prey.get('source', 'web'),
                'region': 'global',
                'category': [], 'scene': [],
                'roles': ['developer'],
                'data_tags': ['fresh', 'needs_review'],
                'reason': '', 'isFavorite': False,
                'captured_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # 自动分类（基于标题关键词初步分类）
            CAT_RULES = [
                (['写作','文案','内容创作','小说','自媒体','爆文'], 'media'),
                (['图像','图片','视频','设计','修图','海报','logo','3d','渲染','绘画'], 'media'),
                (['agent','智能体','自主','自动化','工作流','workflow','bot','机器人'], 'agent'),
                (['llm','大模型','gpt','chatgpt','claude','对话','聊天','prompt','提示词'], 'llm'),
                (['rag','知识库','向量','embedding','搜索','检索','文档问答','pdf','知识'], 'rag'),
                (['开发','代码','编程','ide','框架','cli','部署','git','github','api','sdk'], 'dev-tool'),
                (['数据','分析','bi','报表','统计','机器学习','深度学习','训练','预测'], 'data-science'),
            ]
            text = (name + ' ' + (prey.get('description') or '')).lower()
            assigned = []
            for keywords, cat in CAT_RULES:
                if any(kw in text for kw in keywords):
                    assigned.append(cat)
            item['category'] = assigned if assigned else ['uncategorized']
            
            # ── 硬性校验：5项缺一不可（分类后再校验）──
            violations = []
            if not item['title']: violations.append('title')
            if not item['abstract_zh']: violations.append('abstract_zh')
            if not item['abstract']: violations.append('abstract')
            if not item['category']: violations.append('category')
            if not item['score'] or item['score'] <= 0: violations.append('score')
            if not item['url']: violations.append('url')
            
            if violations:
                log(f'  ⛔ 拒绝: {name[:30]}... 缺字段: {", ".join(violations)}')
                continue
            existing.append(item)
            existing_names.add(name.lower())
            new_count += 1
        except:
            continue
    
    log(f'  ✅ 新增 {new_count} 个工具')
except Exception as e:
    log(f'  ❌ 合并失败: {e}')
    existing = site.get('items', [])  # keep what we have

# ════════════════════════════════════════
# 第四步：重算统计
# ════════════════════════════════════════
log('📊 重算统计...')
region_cnt, source_cnt, cat_cnt, scene_cnt = Counter(), Counter(), Counter(), Counter()
for item in existing:
    s = item.get('score')
    item['score'] = int(s) if s else 0
    region_cnt[item.get('region','unknown')] += 1
    source_cnt[item.get('source','unknown')] += 1
    for c in (item.get('category') or []):
        if c: cat_cnt[c] += 1
    for sc in (item.get('scene') or []):
        if sc: scene_cnt[sc] += 1

site['regions'] = dict(region_cnt.most_common())
site['sources'] = dict(source_cnt.most_common())
site['categories'] = dict(cat_cnt.most_common())
site['scenes'] = dict(scene_cnt.most_common())
site['total'] = len(existing)

# ════════════════════════════════════════
# 第五步：重算推荐
# ════════════════════════════════════════
log('🏆 重算推荐...')
cn = sorted([i for i in existing if i.get('region')=='cn'], key=lambda x: -(x.get('score') or 0))
gl = sorted([i for i in existing if i.get('region')=='global'], key=lambda x: -(x.get('score') or 0))
pm = sorted([i for i in existing if i.get('isFavorite')], key=lambda x: -(x.get('score') or 0))

site['trending'] = (gl[:4] + cn[:4])[:8]
site['daily_picks'] = (gl[:3] + cn[:2])[:5]
site['today_recommends'] = pm[:3]
site['updated_at'] = time.strftime('%Y-%m-%d %H:%M:%S')

# 清理多余字段
for lst in ['trending','daily_picks','today_recommends']:
    for item in site.get(lst, []):
        for k in ['name','description','slug']:
            item.pop(k, None)

site['items'] = existing
json.dump(site, open(SITE_DATA, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
log(f'  ✅ data.json 已更新 ({len(existing)} 个工具)')

# 创建部署标志
open(FLAG_FILE, 'w').write(f'部署就绪 | {time.strftime("%Y-%m-%d %H:%M")} | {len(existing)}个工具')
log(f'  🚩 部署标志已创建')

print(f'\n  ✅ 每日刷新完成！共 {len(existing)} 个工具')
print(f'  💡 下次会话时曦和会自动检测部署标志并更新CDN')
