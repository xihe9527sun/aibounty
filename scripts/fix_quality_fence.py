#!/usr/bin/env python3
"""
数据质量防火墙 v2
==================
在 curate_and_dedup 之后运行，执行数据质量铁律第7条、第8条的自动化检查与修复。

功能：
  1. 标题清洗 — 去除 "Show HN:" / "Ask HN:" / "Tell HN:" / "Launch HN:" 等非工具前缀
  2. 垃圾检测 — 标记讨论帖（描述仅为 "HN discussion (X pts)"）
  3. 描述修复 — 对垃圾工具自动补充"暂无详细描述"占位
  4. 推荐重筛 — today_recommends 只保留干净工具
  5. 输出报告

用法:
  python scripts/fix_quality_fence.py              # 预览模式
  python scripts/fix_quality_fence.py --fix         # 执行修复
"""
import json, os, sys, re
from collections import Counter

DATA_PATH = r'E:\ToolPilot\site\data.json'
DO_FIX = '--fix' in sys.argv

# ── 垃圾检测规则 ──
HN_PREFIXES = ('show hn:', 'ask hn:', 'tell hn:', 'launch hn:', 'show hn ：', 'ask hn ：')
GARBAGE_ABSTRACT_PATTERNS = ('hn discussion', 'hn hot', 'ask hn', 'show hn')
ABSTRACT_MIN_WORDS = 15     # 英文最少词数
ABSTRACT_MIN_CHARS_ZH = 20  # 中文最少字数

# 从 title 中去除 HN 前缀的正则
HN_PREFIX_RE = re.compile(r'^(Show|Ask|Tell|Launch)\s+HN\s*[：:]\s*', re.IGNORECASE)

def clean_title(title):
    """去除 'Show HN:' 等前缀，保留后半部分"""
    return HN_PREFIX_RE.sub('', title).strip()

def is_garbage_title(title):
    t = title.strip().lower()
    return any(t.startswith(p) for p in HN_PREFIXES)

def is_garbage_abstract(abstract):
    a = abstract.strip().lower()
    if any(p in a for p in GARBAGE_ABSTRACT_PATTERNS):
        if len(abstract) < 30:
            return True
    if len(a) < 12 and not any('\u4e00' <= c <= '\u9fff' for c in abstract):
        return True
    return False

def classify_tool(item):
    """返回工具的质量等级: clean / garbage / needs_review"""
    title = item.get('title', '')
    abstract = item.get('abstract', '')
    abstract_zh = item.get('abstract_zh', '')

    issues = []
    if is_garbage_title(title):
        issues.append('garbage_title')
    elif is_garbage_abstract(abstract):
        issues.append('garbage_abstract')

    en_words = len(abstract.split())
    zh_chars = len([c for c in abstract_zh if '\u4e00' <= c <= '\u9fff'])
    if en_words < ABSTRACT_MIN_WORDS:
        issues.append(f'short_en({en_words}w)')
    if zh_chars < ABSTRACT_MIN_CHARS_ZH:
        issues.append(f'short_zh({zh_chars}c)')

    if not issues:
        return 'clean'
    elif 'garbage_title' in issues or 'garbage_abstract' in issues:
        return 'garbage'
    else:
        return 'needs_review'


# ═══════════════════════════════════════
#  主流程
# ═══════════════════════════════════════
with open(DATA_PATH, 'r', encoding='utf-8') as f:
    data = json.load(f)

items = data['items']
item_map = {i['id']: i for i in items}

results = {'clean': [], 'garbage': [], 'needs_review': []}
title_fixes = 0  # 标题前缀清理计数
desc_fixes = 0   # 描述占位修复计数

for item in items:
    level = classify_tool(item)
    results[level].append(item['id'])

# ── 打印统计 ──
print('=' * 60)
print('  AIbounty 数据质量扫描报告 v2')
print('=' * 60)
print(f'  总工具数: {len(items)}')
print(f'  来源: HN={sum(1 for t in items if t.get("source")=="hn")}' +
      f'  GitHub={sum(1 for t in items if t.get("source") in ("github","github_trending"))}' +
      f'  nav={sum(1 for t in items if t.get("source")=="nav_hunter")}')
print()
print(f'  [CLEAN]            {len(results["clean"]):>5}')
print(f'  [NEEDS_REVIEW]     {len(results["needs_review"]):>5}')
print(f'  [GARBAGE]          {len(results["garbage"]):>5}')
print()

# ── 执行修复 ──
if DO_FIX:
    print('━' * 60)
    print('  执行修复...')
    print()

    # 1. 标题清洗：去除 HN 前缀
    for item in items:
        old_title = item.get('title', '')
        new_title = clean_title(old_title)
        if new_title != old_title:
            item['title'] = new_title
            title_fixes += 1
            if title_fixes <= 5:
                print(f'  [TITLE] "{old_title[:60]}"')
                print(f'       -> "{new_title[:60]}"')

    # 2. 垃圾工具标记
    for tid in results['garbage']:
        item = item_map[tid]
        tags = item.get('data_tags', [])
        if isinstance(tags, list):
            if '__garbage__' not in tags:
                tags.append('__garbage__')
                item['data_tags'] = tags
        item['_quality_flag'] = 'garbage'

        # 对垃圾工具，如果描述是HN元数据，补上占位描述
        abstract = item.get('abstract', '')
        abstract_zh = item.get('abstract_zh', '')
        if is_garbage_abstract(abstract) or is_garbage_abstract(abstract_zh):
            if not abstract or is_garbage_abstract(abstract):
                item['abstract'] = 'No detailed description yet. This tool is pending review.'
                desc_fixes += 1
            if not abstract_zh or is_garbage_abstract(abstract_zh):
                item['abstract_zh'] = '暂无详细描述，该工具正在审核中。'
                desc_fixes += 1

    # 3. today_recommends 重筛
    recs = data.get('today_recommends', [])
    rec_ids_orig = [r.get('id') if isinstance(r, dict) else r for r in recs]

    clean_ids = set(results['clean']) | set(results['needs_review'])
    rec_ids_new = [tid for tid in rec_ids_orig if tid in clean_ids]

    # 如果不够，从 clean 中按 stars 补充
    MIN_RECS = 3
    if len(rec_ids_new) < MIN_RECS:
        candidates = sorted(
            [item_map[tid] for tid in results['clean'] if tid not in set(rec_ids_new)],
            key=lambda x: -(x.get('stars', 0) or 0)
        )
        for c in candidates:
            rec_ids_new.append(c['id'])
            if len(rec_ids_new) >= MIN_RECS:
                break

    data['today_recommends'] = [{'id': tid, 'type': 'auto'} for tid in rec_ids_new[:3]]

    # 4. trending 清理（如果是 id 列表）
    trend = data.get('trending', [])
    if isinstance(trend, list) and trend and isinstance(trend[0], str):
        data['trending'] = [tid for tid in trend if tid in clean_ids]

    # ── 写回文件 ──
    with open(DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, separators=(',', ':'))

    new_size = os.path.getsize(DATA_PATH)
    print()
    print(f'  [OK] data.json 已更新 ({new_size} bytes)')
    print(f'  [TITLE] 已清洗 {title_fixes} 个 HN 标题前缀')
    print(f'  [DESC]  已修复 {desc_fixes} 个垃圾描述')
    print(f'  [TAG]   {len(results["garbage"])} 个工具已标记 __garbage__')
    print(f'  [RECS]  today_recommends: {len(rec_ids_orig)} → {len(data["today_recommends"])}')
    print()

else:
    # ── 预览报告 ──
    hn_titles = [t for t in items if HN_PREFIX_RE.match(t.get('title', ''))]
    print(f'  待清洗的 HN 标题: {len(hn_titles)}')
    for t in hn_titles[:3]:
        print(f'    - "{t["title"]}"')

    print()
    print(f'  today_recommends 当前: {len(data.get("today_recommends",[]))} 个')
    print()
    print('  [PREVIEW] 未加 --fix 参数，未做任何修改。')
    print('            加 --fix 执行修复：python scripts/fix_quality_fence.py --fix')

print('=' * 60)
