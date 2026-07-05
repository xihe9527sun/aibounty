#!/usr/bin/env python3
"""修复 data.json 中所有工具的 region 字段
- nav_hunter/juejin/gitee/sspai 来源 → cn（中国站点/中国产工具）
- 其余 N/A → global
"""
import json, os, re
from collections import Counter

DATA_PATH = r'E:\ToolPilot\site\data.json'

with open(DATA_PATH, 'r', encoding='utf-8') as f:
    data = json.load(f)

items = data['items']
changed = 0

# 国内来源白名单：nav_hunter=ai-bot.cn中文导航站, juejin=掘金, gitee=码云, sspai=少数派
CN_SOURCES = {'nav_hunter', 'juejin', 'gitee', 'sspai'}

for item in items:
    old = item.get('region', 'N/A')
    source = item.get('source', '')

    # 规则1：N/A → 按来源推断
    if old == 'N/A':
        if source in CN_SOURCES:
            item['region'] = 'cn'
        else:
            item['region'] = 'global'
        changed += 1
        continue

    # 规则2：全球来源误标为 cn 的修正（极少，仅做防御）
    if old == 'cn' and source not in CN_SOURCES and source not in ('github_trending',):
        item['region'] = 'global'
        changed += 1
        continue

    # 规则3：nav_hunter 来源被误标为 global → 修正为 cn
    if old == 'global' and source in CN_SOURCES:
        item['region'] = 'cn'
        changed += 1
        continue

# 重算 regions 元数据
region_counts = Counter(i.get('region', 'global') for i in items)
data['regions'] = dict(region_counts.most_common())

cn_count = sum(1 for i in items if i.get('region') == 'cn')
print(f'工具总数: {len(items)}')
print(f'region=cn: {cn_count}')
print(f'region=global: {sum(1 for i in items if i.get("region") == "global")}')
print(f'修改条数: {changed}')
print(f'regions元数据: {data["regions"]}')

with open(DATA_PATH, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, separators=(',', ':'))

new_size = os.path.getsize(DATA_PATH)
print(f'[OK] data.json 已更新 ({new_size} bytes)')
