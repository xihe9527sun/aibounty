#!/usr/bin/env python3
"""AIbounty 智能标签系统 v2 — 三层标签体系 + AI分类 + Graveyard
用法:
  python scripts/auto_tag_v2.py                   # 全量打标
  python scripts/auto_tag_v2.py --dry-run          # 预览不打标
  python scripts/auto_tag_v2.py --report           # 只看统计
"""
import json, sys, os, re, math
from datetime import datetime, timezone

DATA_FILE = 'site/data.json'
DEAD_CACHE = 'reports/dead_links_cache.json'

# ─── 启发式标签规则 ───

# 价格模型关键词
PRICE_RULES = [
    (r'free|免费|试用|trial|open.?source|开源', 'open-source'),
    (r'freemium|免费增值|limited.*free|免费.*限制', 'freemium'),
    (r'paid|付费|subscription|订阅|\$[0-9]|pricing|pro|premium|business|enterprise|team|每月|每年|元/月', 'paid'),
]

# 使用场景关键词
SCENE_RULES = [
    (r'code|编程|开发|ide|debug|terminal|cli|command|git|deploy|devops|testing|api|sdk|函数|function', 'code'),
    (r'write|写作|writing|文章|文案|copy|blog|essay|content|story|故事|小说|剧本|report|周报', 'writing'),
    (r'image|图片|图像|photo|画图|绘画|design|设计|illustration|插画|logo|海报|brand|素材|创意|art|艺术', 'image'),
    (r'video|视频|film|movie|animation|动画|短片|剪辑|edit.*video', 'video'),
    (r'audio|audio|语音|voice|speech|音乐|music|song|播客|podcast|sound', 'audio'),
    (r'chat|对话|聊天|assistant|助手|bot|客服|customer.*service|support|问答|qa', 'chat'),
    (r'data|数据分析|data.*science|analytics|dashboard|报表|bi|可视化|visualization|chart|图表', 'data'),
    (r'automation|自动化|workflow|流程|pipeline|trigger|action|zapier|n8n|ifttt', 'automation'),
    (r'research|研究|科研|paper|论文|arxiv|academic|学术|survey|综述|experiment', 'research'),
    (r'business|商业|营销|marketing|sales|销售|crm|finance|金融|trading|交易|hr|招聘|recruit', 'business'),
    (r'education|教育|学习|learn|course|课程|tutorial|教学|training', 'education'),
    (r'game|游戏|gaming|3d|建模|modeling|avatar|虚拟|virtual|ar|vr|元宇宙|metaverse', 'game'),
]

# 子分类映射（从category+关键词推导）
SUBCAT_MAP = {
    'agent': {
        'agent': 'ai-agent',
        'multi-agent|多智能体|团队|swarm|orchestrat': 'multi-agent',
        'framework|框架|platform|平台|builder|搭建|构建': 'agent-framework',
    },
    'llm': {
        'chat|对话|chatbot|gpt|claude|gemini|deepseek|qwen|chat': 'ai-chat',
        'embedding|vector|向量|检索|search|搜索|rerank': 'embedding-search',
        'train|训练|fine.?tune|微调|model.*hub|模型.*库': 'model-training',
        'api|sdk|gateway|proxy|router|路由|代理': 'llm-api',
    },
    'rag': {
        'rag|检索|retrieval|knowledge|知识库|qa.*doc|文档.*问答': 'rag-framework',
        'vector.*db|向量.*数据库|chroma|pinecone|weaviate|qdrant|milvus': 'vector-database',
        'document|文档|pdf|parsing|解析|chunk|分块|pipeline|处理': 'document-pipeline',
    },
    'dev-tool': {
        'ide|editor|编辑器|cursor|windsurf|vscode|vim|neovim|jetbrain': 'ide',
        'code.*assist|编程.*助手|code.*review|代码.*审查|pair.*prog': 'code-assistant',
        'devops|ci/cd|deploy|部署|docker|k8s|kubernetes|container': 'devops',
        'testing|测试|debug|调试|bug|修复|qa|quality': 'testing-debug',
        'cli|terminal|终端|command|命令行|shell|bash': 'cli-terminal',
    },
    'media': {
        'image.*gen|图片.*生成|text.*to.*image|文生图|stable.?diffusion|midjourney|dalle': 'image-generation',
        'video.*gen|视频.*生成|text.*to.*video|文生视频|runway|sora|pika|veo|kling|可灵': 'video-generation',
        'audio.*gen|audio|音乐|music|tts|text.*to.*speech|语音|voice|播客': 'audio-generation',
        'design|设计|figma|sketch|ui|ux|原型|prototype|canva|排版': 'design-tools',
        'edit|编辑|修图|retouch|enhance|增强|upscale|放大|restore|修复': 'image-editing',
    },
    'data-science': {
        'analysis|分析|analytics|统计|statistics|pandas|numpy|jupyter': 'data-analysis',
        'visualization|可视化|chart|图表|dashboard|报表|plot|graph': 'data-visualization',
        'ml|machine.?learn|深度学习|deep.?learn|pytorch|tensorflow|模型|训练': 'ml-platform',
        'trading|量化|quant|finance|金融|stock|股票|投资|market|市场': 'quant-trading',
    },
}


def heuristic_price(text):
    """从文本中推断价格模型（只用title，避免abstract的AI模板干扰）"""
    text_lower = text.lower()
    for pattern, tag in PRICE_RULES:
        if re.search(pattern, text_lower, re.IGNORECASE):
            if tag == 'open-source': return 'open-source'
            if tag == 'freemium': return 'freemium'
            if tag == 'paid': return 'paid'
    # GitHub项目默认开源
    return 'unknown'


def heuristic_scenes(title, category):
    """从文本中提取使用场景（只用title+category，不用abstract避免AI模板干扰）"""
    text = f"{title} {category}"
    text_lower = text.lower()
    scenes = []
    for pattern, tag in SCENE_RULES:
        if re.search(pattern, text_lower, re.IGNORECASE):
            if tag not in scenes:
                scenes.append(tag)
    return scenes


def heuristic_subcat(category, title):
    """推导子分类"""
    if isinstance(category, str):
        cats = [category]
    else:
        cats = category or []
    text = title.lower()
    subcats = []
    for cat in cats:
        cat_map = SUBCAT_MAP.get(cat, {})
        for pattern, subcat in cat_map.items():
            if re.search(pattern, text, re.IGNORECASE):
                if subcat not in subcats:
                    subcats.append(subcat)
    return subcats


def star_tier(score):
    """GitHub star等级标签"""
    try:
        s = int(score)
        if s >= 100000: return 'star-100k'
        if s >= 10000: return 'star-10k'
        if s >= 1000: return 'star-1k'
        if s >= 100: return 'star-100'
    except: pass
    return None


def fresh_tag(captured_at):
    """新鲜度标签"""
    if not captured_at:
        return None
    try:
        cap = datetime.strptime(captured_at.replace('T', ' ')[:19], '%Y-%m-%d %H:%M:%S')
        now = datetime.now()
        days = (now - cap).days
        if days <= 3: return 'hot-new'
        if days <= 7: return 'fresh'
        if days <= 30: return 'recent'
    except: pass
    return None


def load_data():
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_dead_links():
    if not os.path.exists(DEAD_CACHE):
        return {}
    with open(DEAD_CACHE, 'r', encoding='utf-8') as f:
        return json.load(f)


def is_dead_link(item, dead_cache):
    """判断是否死链"""
    item_id = str(item.get('id', ''))
    if item_id in dead_cache:
        code = dead_cache[item_id].get('code', 200)
        return code < 0 and code != -2  # code=-5真死, code=-1无URL
    return False


def main():
    dry_run = '--dry-run' in sys.argv
    report_only = '--report' in sys.argv

    data = load_data()
    items = data['items']
    dead_cache = load_dead_links()

    # ─── 统计报告 ───
    stats = {
        'total': len(items),
        'price_models': {},
        'scenes': {},
        'subcats': {},
        'radar_tags': {},
        'dead_count': 0,
        'uncategorized_fixed': 0,
        'total_new_tags': 0,
    }

    for item in items:
        if report_only:
            continue

        title = item.get('title', '')
        abstract = item.get('abstract', '')
        abstract_zh = item.get('abstract_zh', '')
        combined = f"{title} {abstract} {abstract_zh}"
        # 只用title进行价格检测（abstract的AI模板噪声太大）
        price_text = title
        category = item.get('category', [])
        if isinstance(category, str):
            try: category = json.loads(category)
            except: category = [category]
        score = item.get('score', 0)
        captured_at = item.get('captured_at', '')
        source = item.get('source', '')
        old_tags = item.get('data_tags', [])

        # 保留已有有价值的标签
        preserved_tags = []
        if isinstance(old_tags, list):
            for t in old_tags:
                if t in ('has_demo', 'enterprise_grade', 'needs_review', 'popular', 'fresh'):
                    preserved_tags.append(t)
                # 保留所有中文标签（它们是人工标的）
                if re.match(r'^[\u4e00-\u9fff]', str(t)):
                    preserved_tags.append(t)

        new_tags = list(preserved_tags)

        # 1. 价格标签
        price = heuristic_price(price_text)
        # GitHub/Gitee项目标记为开源（除非标题明确标了付费）
        if source in ('github', 'gitee') and price == 'unknown' and 'price-paid' not in price_text:
            price = 'open-source'
        if price != 'unknown' and price not in new_tags:
            new_tags.append(f'price-{price}')
        stats['price_models'][price] = stats['price_models'].get(price, 0) + 1

        # 2. 使用场景标签（只从title+category提取）
        scenes = heuristic_scenes(title, category)
        for s in scenes:
            tag = f'scene-{s}'
            if tag not in new_tags:
                new_tags.append(tag)
            stats['scenes'][s] = stats['scenes'].get(s, 0) + 1

        # 3. 子分类标签
        subcats = heuristic_subcat(category, title)
        for sc in subcats:
            if sc not in new_tags:
                new_tags.append(sc)
            stats['subcats'][sc] = stats['subcats'].get(sc, 0) + 1

        # 4. 技术雷达标签
        # Star等级
        st = star_tier(score)
        if st and st not in new_tags:
            new_tags.append(st)
            stats['radar_tags'][st] = stats['radar_tags'].get(st, 0) + 1

        # 新鲜度
        ft = fresh_tag(captured_at)
        if ft and ft not in new_tags:
            # 替换旧版fresh标签
            new_tags = [t for t in new_tags if t != 'fresh']
            new_tags.append(ft)
            stats['radar_tags'][ft] = stats['radar_tags'].get(ft, 0) + 1

        # 来源认证标签
        if source == 'github':
            t = 'source-github'
            if t not in new_tags: new_tags.append(t)
        elif source == 'hn':
            t = 'source-hn'
            if t not in new_tags: new_tags.append(t)
        elif source == 'producthunt':
            t = 'source-ph'
            if t not in new_tags: new_tags.append(t)
        elif source == 'gitee':
            t = 'source-gitee'
            if t not in new_tags: new_tags.append(t)

        # 5. Graveyard状态
        if is_dead_link(item, dead_cache):
            if 'status-dead' not in new_tags:
                new_tags.append('status-dead')
            stats['dead_count'] += 1

        # 6. 高星认证（已有high_stars，但标准化）
        try:
            if int(score) > 10000 and 'star-certified' not in new_tags:
                new_tags.append('star-certified')
        except: pass

        # 7. 如果是github项目且有score，推定为open-source
        if source == 'github' and 'price-open-source' not in new_tags and price == 'unknown':
            new_tags.append('price-open-source')
            stats['price_models']['open-source'] = stats['price_models'].get('open-source', 0) + 1

        # 更新item
        item['data_tags'] = new_tags
        
        # 添加price_model字段（给前端直接使用）
        item['price_model'] = price

        # 统计
        added = len(new_tags) - len(preserved_tags)
        stats['total_new_tags'] += added

    if report_only:
        # 只打印报告
        pass

    if dry_run:
        print(f"[DRY RUN] 将更新 {len(items)} 个工具")
        print(f"  ├ 新增标签: {stats['total_new_tags']} 个")
        print(f"  ├ 死链标记: {stats['dead_count']} 个")
        print(f"  └ 价格模型: {stats['price_models']}")
        print(f"\n场景标签分布:")
        for k, v in sorted(stats['scenes'].items(), key=lambda x: -x[1]):
            print(f"  {k}: {v}")
        print(f"\n子分类分布:")
        for k, v in sorted(stats['subcats'].items(), key=lambda x: -x[1]):
            print(f"  {k}: {v}")
        print(f"\n雷达标签分布:")
        for k, v in sorted(stats['radar_tags'].items(), key=lambda x: -x[1]):
            print(f"  {k}: {v}")
        return

    # 保存
    save_data(data)
    print(f"[OK] 打标完成: {len(items)} 个工具")
    print(f"  ├ 新增标签: {stats['total_new_tags']} 个")
    print(f"  ├ 死链标记: {stats['dead_count']} 个")
    print(f"  ├ 价格模型: {stats['price_models']}")
    print(f"  └ 子分类新增: {len(stats['subcats'])} 种子分类")


if __name__ == '__main__':
    main()
