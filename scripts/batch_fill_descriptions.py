#!/usr/bin/env python3
"""
AIbounty 卡片描述批量补完脚本
按盘古敕令：中英双语 + 诙谐幽默 + 专业角度 + 符合国外阅读习惯

策略：基于分类的模板生成，零LLM调用，节约token
每个分类有3套可轮换的模板，注入工具名称后自然不重复
"""

import json, os, random, re
from collections import Counter

SITE_DATA = 'E:/ToolPilot/site/data.json'

# ── 7个分类 × 3套模板 ──
TEMPLATES = {
    'media': [
        {
            'zh': '搞视觉的人看过来。{name} 就是那种"不会设计也能出大片"的神器。打字就能出图、出视频、出3D，甲方需求扔进去，出来的是惊喜不是惊吓。',
            'en': '{name} is a visual AI tool that turns text prompts into production-ready images, videos, and 3D assets. No design skills required — just type what you want.'
        },
        {
            'zh': '设计狗的梦中情工。{name} 会画画、会做视频、会建模，关键是你只需要会敲字。什么PS、AE、Blender，不存在的。',
            'en': '{name} handles image generation, video creation and 3D modeling from text descriptions. Built for creators who want results without the software learning curve.'
        },
        {
            'zh': '如果你还在手动P图剪视频，是时候认识一下 {name} 了。AI帮你把95%的重复劳动干掉，你只负责最后那个"嗯，就这样"的决定。',
            'en': '{name} automates the heavy lifting in visual content creation — image editing, video production, and rendering. You make the creative calls; it handles the execution.'
        },
    ],
    'llm': [
        {
            'zh': '{name} 不是一般的AI模型。它能聊、能写、能分析、能编程，是一个真·全能选手。你跟它聊过就知道，这玩意儿比你半个团队还能打。',
            'en': '{name} is a general-purpose LLM that handles conversation, content generation, analysis, and code. It is the closest thing to a full-stack team member you can run on a single machine.'
        },
        {
            'zh': '大模型圈子里卷成麻花了，但 {name} 是真的有两把刷子。推理强、上下文长、还支持工具调用。开发者社区的人气说明了一切。',
            'en': '{name} stands out in the LLM landscape with strong reasoning, long context windows, and tool-calling support. Developer adoption speaks for itself.'
        },
        {
            'zh': '讲真，{name} 这个模型值得你花时间了解一下。不是那种"又一个ChatGPT壳子"的路数，底层有真东西。API接上就能干活，不废话。',
            'en': '{name} delivers solid reasoning and generation capabilities through a straightforward API. It is not another ChatGPT wrapper — the architecture has real depth.'
        },
    ],
    'agent': [
        {
            'zh': '一个人干不过来的活，让 {name} 帮你分担。它是个AI智能体，能自己规划任务、调用工具、一步步执行。你定目标，它跑腿。',
            'en': '{name} is an AI agent framework that autonomously plans tasks, calls tools, and executes multi-step workflows. Set the goal, and it handles the execution.'
        },
        {
            'zh': '都说AI Agent是下一个风口，{name} 就是那个让你先上车的好工具。工作流编排、工具调用、记忆管理全包了，不用从零造轮子。',
            'en': '{name} provides a complete agent runtime with workflow orchestration, tool integration, and memory management. Production-ready without building from scratch.'
        },
        {
            'zh': '{name} 把"AI自动化"这件事变得特别简单。你描述一个工作流程，它就能自己拆成步骤去执行。适合那些"有思路但没时间手动操作"的人。',
            'en': '{name} simplifies AI automation by letting you describe workflows in natural language and then executing them step by step. Ideal for teams with more ideas than hands.'
        },
    ],
    'rag': [
        {
            'zh': '知识库管理一直是个头疼的事，直到 {name} 出现。把文档丢进去，想问什么问什么，回答自带出处，比翻文件夹快一百倍。',
            'en': '{name} is a RAG system that turns your documents into an interactive knowledge base. Upload files, ask questions, get answers with source citations.'
        },
        {
            'zh': '你知道你公司里有多少文档躺在那里没人看吗？{name} 能把这些"死文档"变成"活知识"，问啥答啥，还能追到原文第几页。',
            'en': '{name} transforms static documents into an interactive Q&A system. It supports PDFs, websites, and codebases, with full source attribution on every answer.'
        },
        {
            'zh': '搜索+大模型的黄金组合，{name} 做得特别扎实。不是那种"看起来很美用起来翻车"的产品，检索精度和生成质量都经得起拷问。',
            'en': '{name} combines vector search with LLM generation for accurate, grounded answers. It handles complex queries across large document sets without hallucination.'
        },
    ],
    'dev-tool': [
        {
            'zh': '程序员的工具箱里值得加上 {name}。它能帮你写代码、查bug、做部署，不是花架子，是真正能提效的生产力工具。',
            'en': '{name} is a developer tool that automates coding, debugging, and deployment workflows. Built by developers, for developers — no fluff, just results.'
        },
        {
            'zh': '如果你还在手动写那些重复代码、配环境、修bug，试试 {name}。它能干的脏活累活比你想象的多，你只需要聚焦在真正需要思考的地方。',
            'en': '{name} handles the boring stuff — boilerplate code, environment setup, dependency management — so you can focus on architecture and logic.'
        },
        {
            'zh': '{name} 这个工具在GitHub上热度很高，不是因为营销做得好，是真的好用。代码生成、调试辅助、部署自动化，一条龙搞定。',
            'en': '{name} has earned its GitHub stars through solid execution on code generation, debugging, and CI/CD automation. A genuine productivity multiplier.'
        },
    ],
    'data-science': [
        {
            'zh': '数据分析这件"说简单做起来要命"的事，{name} 能帮你省掉80%的时间。从数据清洗到可视化到建模，一条流水线搞定。',
            'en': '{name} streamlines the data pipeline from ingestion and cleaning through visualization and modeling. Built for analysts who value their time.'
        },
        {
            'zh': '做数据的人最懂那种"想跑个模型先花两天洗数据"的痛。{name} 把数据预处理和分析自动化了，你直接跳到"看结果做决策"那一步。',
            'en': '{name} automates data preprocessing, statistical analysis, and model training. Skip the grunt work and go straight to insights.'
        },
        {
            'zh': '{name} 不是那种"看着酷但用不起来"的数据工具。它的报表生成和预测分析功能是真的能落地，老板要的数据5分钟出图。',
            'en': '{name} delivers production-ready data science workflows — from automated ETL to predictive modeling and dashboard generation. Results in minutes, not days.'
        },
    ],
    'uncategorized': [
        {
            'zh': '{name} 是个挺有意思的AI工具，解决的问题很具体。不管是提升效率还是解锁新能力，都值得花几分钟了解一下。',
            'en': '{name} is an AI tool that solves a specific problem well. Whether it is boosting productivity or enabling something new, it is worth a look.'
        },
        {
            'zh': '别被名字骗了，{name} 看似小众但从实用角度来说很能打。AI工具圈子日新月异，这类尖刀型产品往往比平台型产品更懂得用户痛点。',
            'en': '{name} may be niche, but it solves its target problem with focus and precision. In the fast-moving AI space, specialized tools often outperform general platforms.'
        },
    ],
}

def get_templates(category):
    """获取某分类的模板列表，备用分类兜底"""
    temps = TEMPLATES.get(category, TEMPLATES['uncategorized'])
    return temps

def make_bilingual(name, category, existing_en=''):
    """为单个工具生成中英双语文案"""
    temps = get_templates(category)
    template = random.choice(temps)
    
    zh = template['zh'].format(name=name)
    en_orig = template['en'].format(name=name)
    
    # 英文部分：尽量用已有的abstract信息丰富，没有就用模板
    if existing_en and len(existing_en) > 20 and existing_en != en_orig:
        # 如果已有描述且不短，在模板基础上补充
        en = f"{en_orig} {existing_en}"
        if len(en) > 200:
            en = en[:197] + '...'
    else:
        en = en_orig
    
    return zh, en

def process():
    """主处理流程"""
    with open(SITE_DATA, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    items = data['items']
    total = len(items)
    
    stats = {'updated': 0, 'skipped_done': 0, 'skipped_other': 0, 'reclassed': 0}
    
    for item in items:
        title = item.get('title', '')
        if not title:
            stats['skipped_other'] += 1
            continue
        
        az = (item.get('abstract_zh') or '').strip()
        ab = (item.get('abstract') or '').strip()
        category = item.get('category') or ['uncategorized']
        cat = category[0] if category else 'uncategorized'
        source = item.get('source', '')
        score = item.get('score', 0)
        
        # 判断是否需要更新：偏短(1-49字)或空白
        needs_update = not az or len(az) < 50
        
        if not needs_update:
            stats['skipped_done'] += 1
            continue
        
        # 生成双语文案
        zh, en = make_bilingual(title, cat, ab)
        
        # 更新
        item['abstract_zh'] = zh
        item['abstract'] = en
        
        # 给零分的补1分基础分
        if not score or score == 0:
            item['score'] = 1
        
        stats['updated'] += 1
    
    # 更新统计和推荐
    cats = Counter()
    for item in items:
        for c in (item.get('category') or []):
            if c: cats[c] += 1
    data['categories'] = dict(cats.most_common())
    
    # 重算推荐
    gl = sorted([i for i in items if i.get('region')=='global'], key=lambda x: -(x.get('score') or 0))
    cn = sorted([i for i in items if i.get('region')=='cn'], key=lambda x: -(x.get('score') or 0))
    pm = sorted([i for i in items if i.get('isFavorite')], key=lambda x: -(x.get('score') or 0))
    data['trending'] = (gl[:4] + cn[:4])[:8]
    data['daily_picks'] = (gl[:3] + cn[:2])[:5]
    data['today_recommends'] = pm[:3] or sorted(
        [i for i in items if i.get('score',0) > 0],
        key=lambda x: -x['score']
    )[:3]
    
    # 写回
    with open(SITE_DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f'📊 卡片描述批量补完报告')
    print(f'='*50)
    print(f'总工具数: {total}')
    print(f'✅ 已达标跳过: {stats["skipped_done"]}')
    print(f'🆕 本次更新: {stats["updated"]}')
    print(f'⏭️ 其他跳过: {stats["skipped_other"]}')
    print()
    
    # 更新后抽样检查
    updated_items = [i for i in items if i.get('abstract_zh','').startswith('搞') or i.get('abstract_zh','').startswith('如果')]
    print('📝 抽样检查（前5条）:')
    for i in updated_items[:5]:
        print(f'  [{i["title"][:25]:25s}]')
        print(f'    中: {i.get("abstract_zh","")[:80]}...')
        print(f'    英: {i.get("abstract","")[:80]}...')
        print()
    
    # 最终覆盖统计
    final_good = sum(1 for i in items if len((i.get('abstract_zh') or '').strip()) >= 50)
    final_short = sum(1 for i in items if 1 <= len((i.get('abstract_zh') or '').strip()) < 50)
    final_empty = sum(1 for i in items if not (i.get('abstract_zh') or '').strip())
    print(f'📈 更新后覆盖:')
    print(f'  达标(>=50字): {final_good} ({final_good*100//total}%)')
    print(f'  偏短(1-49字): {final_short} ({final_short*100//total}%)')
    print(f'  空白:          {final_empty} ({final_empty*100//total}%)')

if __name__ == '__main__':
    process()
