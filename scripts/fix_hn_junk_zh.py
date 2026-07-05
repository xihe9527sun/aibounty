#!/usr/bin/env python3
"""fix_hn_junk_zh.py — 修复 HN 工具中被写为"HN讨论（X分）"的垃圾中文描述

问题：48 个 HN 工具的 abstract_zh 字段被错误地写成了 "HN讨论（X分）"
方案：基于已有的英文 abstract，用 Ollama 翻译/重写成符合风格的中文

用法：python scripts/fix_hn_junk_zh.py [--dry-run]
"""

import json
import os
import re
import sys
import time
import urllib.request
import urllib.error

DATA_JSON = os.path.join(os.path.dirname(__file__), '..', 'site', 'data.json')
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5:3b"

# 垃圾模式
JUNK_PATTERNS = [
    r'^HN\s*(讨论|discussion)',
    r'^HN\s*hot',
    r'^\d+\s*(pts?|points?)[\s）)]',
]

PROMPT_TEMPLATE = """你是一个AI工具导航站的文案编辑。请将以下英文工具描述翻译为**诙谐幽默、口语化的中文**。

规则：
- 中文长度 >= 50字
- 口语化、有画面感、接地气（像给朋友推荐）
- 技术术语保留英文不翻译
- 不要用"随着""值得一提的是""总而言之""解决方案""必不可少"等套话
- 开头要有代入感或反常识观点

英文原文：
{abstract}

只输出翻译后的中文描述，不要任何解释或前缀。"""


def is_junk_zh(text):
    if not text or len(text.strip()) < 10:
        return True
    for p in JUNK_PATTERNS:
        if re.search(p, text, re.IGNORECASE):
            return True
    return False


def is_junk_en(text):
    """Check if English abstract is a junk HN title"""
    if not text or len(text.strip()) < 10:
        return True
    en_patterns = [
        r'^Show\s+HN', r'^Ask\s+HN', r'^Tell\s+HN',
        r'^HN\s*(discussion|show|ask|tell)', r'^\d+\s*pts?',
        r'^HN:', r'^HN\s+\w',
    ]
    for p in en_patterns:
        if re.search(p, text, re.IGNORECASE):
            return True
    return False


def call_ollama(prompt, max_retries=2):
    for attempt in range(max_retries + 1):
        try:
            body = json.dumps({
                "model": MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.85, "num_predict": 200}
            }).encode('utf-8')
            req = urllib.request.Request(OLLAMA_URL, data=body,
                                        headers={'Content-Type': 'application/json'},
                                        method='POST')
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read().decode('utf-8'))
                text = result.get('response', '').strip()
                # Clean up common artifacts
                text = re.sub(r'^["\'\`\s]*', '', text)
                text = re.sub(r'["\'\`\s]*$', '', text)
                if len(text) < 20:
                    raise ValueError(f'Response too short: {len(text)} chars')
                return text
        except Exception as e:
            if attempt < max_retries:
                time.sleep(2 * (attempt + 1))
                continue
            print(f'[ERR] Ollama failed after {max_retries + 1} attempts: {e}')
            return None


def main():
    dry_run = '--dry-run' in sys.argv

    with open(DATA_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)

    items = data.get('items', [])
    bad_items = []

    for item in items:
        zh = item.get('abstract_zh', '')
        if is_junk_zh(zh):
            en = item.get('abstract', '')
            if en and not is_junk_en(en):  # only fix if English is good
                bad_items.append(item)

    total = len(bad_items)
    if total == 0:
        print('[OK] No junk abstract_zh found!')
        return 0

    print(f'[INFO] Found {total} tools with junk abstract_zh')

    fixed = 0
    skipped = 0
    errors = []

    for i, item in enumerate(bad_items, 1):
        tid = item.get('id', '?')
        title = (item.get('title', '') or '')[:45]
        old_zh = item.get('abstract_zh', '')
        new_en = item.get('abstract', '')

        print(f'\n[{i}/{total}] {tid} | {title}')
        print(f'  OLD ZH: {old_zh[:50]}...')

        if dry_run:
            print(f'  [DRY-RUN] Would generate new Chinese from EN abstract')
            fixed += 1
            continue

        prompt = PROMPT_TEMPLATE.format(abstract=new_en)
        new_zh = call_ollama(prompt)

        if new_zh:
            item['abstract_zh'] = new_zh
            print(f'  NEW ZH: {new_zh[:70]}...')
            fixed += 1
        else:
            # Fallback: use a generic template based on category
            cat = ', '.join(item.get('category', [])[:2]) or 'AI'
            fallback = f'{title}这个{cat}类工具挺有意思的。如果你在找能提升效率的AI神器，这个值得一试——简单直接，上手快，适合日常使用。'
            item['abstract_zh'] = fallback
            print(f'  FALLBACK: {fallback[:60]}...')
            errors.append(tid)
            fixed += 1

        time.sleep(0.3)  # Rate limit Ollama

    if not dry_run and fixed > 0:
        with open(DATA_JSON, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
        print(f'\n[OK] Fixed {fixed}/{total} tools. Saved to {DATA_JSON}')

        # Also regenerate tool files for affected items
        out_dir = os.path.join(os.path.dirname(__file__), '..', 'site', 'data')
        for item in bad_items:
            tid = item.get('id')
            if tid:
                path = os.path.join(out_dir, f'tool-{tid}.json')
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(item, f, ensure_ascii=False, separators=(',', ':'))
        print(f'[OK] Updated {len(bad_items)} tool-{id}.json files')
    elif dry_run:
        print(f'\n[DRY-RUN] Would fix {total} tools. Run without --dry-run to apply.')

    if errors:
        print(f'\n[WARN] {len(errors)} tools used fallback descriptions: {errors[:10]}')

    return 0


if __name__ == '__main__':
    sys.exit(main())
