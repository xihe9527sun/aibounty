#!/usr/bin/env python3
"""精品打标 — 从1401个工具里筛选出真正的精品"""
import json, re, os

SITE_DATA = r'E:\ToolPilot\site\data.json'

# 全球知名AI品牌（必精）
PREMIUM_BRANDS = [
    'chatgpt', 'claude', 'gemini', 'midjourney', 'dall-e', 'stable diffusion',
    'copilot', 'cursor', 'perplexity', 'elevenlabs', 'runway', 'pika',
    'notion ai', 'gamma', 'canva', 'figma', 'adobe firefly', 'devin',
    'windsurf', 'bolt.new', 'lovable', 'replit', 'v0.dev', 'krea',
    'suno', 'udio', 'hugging face', 'langchain', 'gradio',
    'github copilot', 'openai', 'anthropic', 'meta ai', 'llama',
    'grammarly', 'jasper', 'character.ai', 'ideogram', 'heyGen',
    'descript', 'otter.ai', 'zapier', 'motion', 'consensus',
    'khanmigo', 'duolingo', 'notebooklm', 'heygen', 'recraft',
    'veed.io', 'pictory', 'synthesia', 'invideo', 'fliki',
    'remove.bg', 'upscale.media', 'clipdrop', 'magnific',
    'leonardo.ai', 'playground ai', 'fireflies.ai', 'mem.ai',
    'raycast', 'warp', 'linear', 'cursor', 'codeium',
    'quillbot', 'rytr', 'writesonic', 'copy.ai', 'jasper',
    'taskade', 'monday.com', 'clickup', 'asana',
    'stability ai', 'blackbox', 'tabnine', 'amazon q',
    'huggingface', 'replicate', 'together.ai',
    # 中文知名品牌
    '豆包', '千问', '通义', '文心一言', '讯飞星火', '智谱清言',
    'kimi', 'deepseek', '腾讯元宝', '扣子', 'coze', '即梦',
    '可灵', '堆友', '秒哒', 'liblib', '哩布哩布',
    '通义灵码', '码上飞', '稿定', '美图', '秘塔',
    '百度', '阿里', '腾讯', '字节', '华为', '小米',
    '商汤', '科大讯飞', '快手', '网易', '京东',
]

# 大厂关键词（公司名级别的可信来源）
BIG_CORP_KEYWORDS = [
    '腾讯推出', '阿里推出', '字节推出', '百度推出', '华为推出',
    '科大讯飞', '小米推出', '快手推出', '网易推出', '京东推出',
    '商汤科技', '智谱', '月之暗面', '百川智能', '零一万物',
    '美团', '蚂蚁', '小红书', '哔哩哔哩', '拼多多',
]

# 要排除的类别关键词（太窄众或非工具类）
EXCLUDE_KEYWORDS = [
    '教程', '课程', '学习', '指南', '社区', '论坛',
]

def is_premium(item):
    """判断是否为精品工具"""
    name = (item.get('name') or '').lower().strip()
    desc = (item.get('description') or '').lower().strip()
    url = (item.get('url') or '').lower().strip()
    
    # 品牌直接匹配
    for brand in PREMIUM_BRANDS:
        if brand.lower() in name:
            return True
    
    # 描述中含大厂关键词
    for kw in BIG_CORP_KEYWORDS:
        if kw.lower() in desc or kw.lower() in name:
            return True
    
    # 域名知名（openai.com, google.com 等）
    for domain in ['openai.com', 'anthropic.com', 'stability.ai', 'midjourney.com',
                   'perplexity.ai', 'elevenlabs.io', 'notion.so', 'figma.com',
                   'canva.com', 'runwayml.com', 'descript.com', 'synthesia.io']:
        if domain in url:
            return True
    
    return False

# 加载
data = json.load(open(SITE_DATA, 'r', encoding='utf-8'))
items = data.get('items', [])

premium_count = 0
total = len(items)

for item in items:
    was_fav = item.get('isFavorite', False)
    should_be = is_premium(item)
    item['isFavorite'] = should_be
    if should_be:
        premium_count += 1

data['items'] = items
json.dump(data, open(SITE_DATA, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

print(f'  📊 总工具: {total}')
print(f'  ⭐ 精品标记: {premium_count} ({premium_count/total*100:.1f}%)')
print(f'  📦 普通: {total - premium_count}')
print(f'  ✅ 已更新: {SITE_DATA}')

# 展示精品列表
print(f'\n  ⭐ 精品工具列表:')
for item in items:
    if item.get('isFavorite'):
        desc = (item.get('description') or '')[:40]
        print(f'    ⭐ {item["name"][:25]:25s} | {desc}')
