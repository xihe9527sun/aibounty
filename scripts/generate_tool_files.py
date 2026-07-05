#!/usr/bin/env python3
"""generate_tool_files.py — 将 data.json 拆分为单个工具文件 + 索引文件

输出:
  site/data/tools-index.json  ← 首页轻量索引（仅元数据+摘要截断，用于相似推荐）
  site/data/tool-{id}.json    ← 每个工具的完整详情（~600 bytes/个）

在日更管线中调用：在 data.json 更新后，deploy 之前运行一次。
"""

import json
import os
import sys

DATA_JSON = os.path.join(os.path.dirname(__file__), '..', 'site', 'data.json')
OUT_DIR   = os.path.join(os.path.dirname(__file__), '..', 'site', 'data')

# 索引文件：只保留相似匹配需要的字段，不含大文本
INDEX_FIELDS = ['id', 'source', 'title', 'url', 'score', 'captured_at',
                'category', 'roles', 'scene', 'data_tags', 'grade_label']


def safe_print(msg):
    """GBK 安全的打印，自动转义非 ASCII 字符"""
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode('utf-8', errors='replace').decode('gbk', errors='replace'))


def build_index(item):
    """从完整工具数据提取首页所需的最小字段集"""
    return {f: item[f] for f in INDEX_FIELDS if f in item}


def main():
    # 1. 加载 data.json
    with open(DATA_JSON, 'r', encoding='utf-8') as f:
        raw = json.load(f)

    items = raw.get('items', [])
    if not items:
        safe_print('[ERR] data.json 中没有 items 字段或为空')
        sys.exit(1)

    total = len(items)
    safe_print(f'[OK] 加载 {total} 个工具')

    # 2. 确保输出目录存在
    os.makedirs(OUT_DIR, exist_ok=True)

    # 3. 生成索引（轻量，用于相似推荐+首页列表）
    index = [build_index(item) for item in items]
    index_path = os.path.join(OUT_DIR, 'tools-index.json')
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, separators=(',', ':'))
    index_size = os.path.getsize(index_path)
    safe_print(f'[OK] 索引文件: {index_path} ({index_size:,} bytes, {len(index)} 条)')

    # 4. 生成单个工具文件
    written = 0
    id_errors = []
    for item in items:
        tool_id = item.get('id')
        if not tool_id:
            id_errors.append(item.get('title', '?'))
            continue

        out_path = os.path.join(OUT_DIR, f'tool-{tool_id}.json')
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(item, f, ensure_ascii=False, separators=(',', ':'))
        written += 1

    safe_print(f'[OK] 生成 {written}/{total} 个工具文件 -> {OUT_DIR}/')
    if id_errors:
        safe_print(f'[WARN] {len(id_errors)} 个工具无 ID 已跳过: {", ".join(id_errors[:5])}...')

    # 5. 计算总大小
    total_size = sum(
        os.path.getsize(os.path.join(OUT_DIR, fname))
        for fname in os.listdir(OUT_DIR)
        if os.path.isfile(os.path.join(OUT_DIR, fname))
    )
    safe_print(f'[OK] data/ 目录总大小: {total_size:,} bytes ({total_size/1024:.0f} KB)')

    # 6. 清理旧文件
    extant_ids = {item['id'] for item in items if item.get('id')}
    deleted = 0
    for fname in os.listdir(OUT_DIR):
        if fname.startswith('tool-') and fname.endswith('.json'):
            tid = fname[5:-5]
            if tid not in extant_ids:
                os.remove(os.path.join(OUT_DIR, fname))
                deleted += 1
    if deleted:
        safe_print(f'[CLEAN] 清理 {deleted} 个过期工具文件')

    return 0


if __name__ == '__main__':
    sys.exit(main())
