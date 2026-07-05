#!/usr/bin/env python3
"""
AIbounty 全量工具描述打磨脚本（盘古敕令版）
中英双语 + 诙谐幽默 + 专业角度 + 符合国外阅读习惯

扫描所有工具，识别不达标的描述，用 Ollama 按风格要求重写。
"""
import json, os, re, sys, requests, time

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "site", "data.json")
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5:7b"
RATE_LIMIT = 0.3
SAVE_INTERVAL = 10

# ── 垃圾英文检测 ──
JUNK_PATTERNS = [
    r'^HN\s*(show\s+)?(ask|tell|launch|discussion)',
    r'^Ask\s+HN', r'^Show\s+HN', r'^Tell\s+HN', r'^HN:',
    r'^\d+\s*pts?\b',
]

def is_real_description(text):
    if not text or len(text) < 15:
        return False
    for j in JUNK_PATTERNS:
        if re.match(j, text.strip(), re.I):
            return False
    has_sentence = '.' in text or '?' in text or '!' in text
    if not has_sentence and len(text) < 40:
        return False
    return True

def is_chinese_ok(text):
    if not text:
        return False
    cn = len(re.findall(r'[\u4e00-\u9fff]', text))
    return cn >= 3 and cn >= len(text) * 0.15

def is_humorous_style(text):
    """检测是否已经符合诙谐幽默风格"""
    if not text or not is_chinese_ok(text):
        return False
    markers = ['了', '的', '吧', '啊', '呢', '吗', '嘛', '不是', '就是',
               '那个', '这种', '什么', '怎么', '真的', '不是那种',
               '狗', '神器', '卷', '活儿', '搞', '让', '把你',
               '看过来', '梦中', '值得', '不是一般的', '不是花架子',
               '别被', '讲真', '说到底', '说简单']
    count = sum(1 for m in markers if m in text)
    return count >= 3

def has_template_origin(text):
    """检测是否来自 batch_fill_descriptions 的模板风格"""
    if not text:
        return False
    starters = ['搞', '如果', '别被', '讲真', '说到底', '不是', '都', '你']
    for s in starters:
        if text.strip().startswith(s):
            return True
    return False

def classify(item):
    """对单个工具分类诊断"""
    en = item.get('abstract', '') or ''
    zh = item.get('abstract_zh', '') or ''

    en_ok = is_real_description(en)
    zh_ok = is_chinese_ok(zh) and is_humorous_style(zh)
    zh_missing = not zh or not is_chinese_ok(zh)
    zh_dry = is_chinese_ok(zh) and not is_humorous_style(zh)

    if not en_ok and zh_dry:
        return 'both_bad'      # 英文垃圾 + 中文直译
    elif not en_ok and zh_missing:
        return 'both_missing'  # 英文垃圾 + 中文缺失
    elif not en_ok:
        return 'en_bad'        # 英文垃圾，中文OK
    elif zh_dry:
        return 'zh_dry'        # 中文直译，英文OK
    elif zh_missing:
        return 'zh_missing'    # 中文缺失，英文OK
    else:
        return 'good'          # 都达标

def call_ollama(prompt, retries=2):
    for attempt in range(retries):
        try:
            resp = requests.post(OLLAMA_URL, json={
                "model": MODEL, "prompt": prompt,
                "stream": False, "options": {"temperature": 0.7, "num_predict": 600}
            }, timeout=120)
            if resp.status_code == 200:
                return (resp.json().get("response") or "").strip()
            print(f"  [WARN] HTTP {resp.status_code}")
        except Exception as e:
            print(f"  [WARN] {e}")
        time.sleep(1)
    return None

def build_both_prompt(item):
    """为完全需要重写的工具生成双语文案"""
    title = item.get('title', '')
    cat = (item.get('category') or [''])[0] or 'uncategorized'
    source = item.get('source', '')
    extra = item.get('abstract', '')[:200]
    if not extra or not is_real_description(extra):
        extra = f'来源: {source}'

    return f"""你是一个专业的AI工具文案专家。请为以下AI工具生成中英双语的精彩描述。

工具名称：{title}
工具分类：{cat}
参考信息：{extra}

要求：
1. 【中文】口语化、诙谐幽默、有画面感、接地气，用"你"拉近读者距离
2. 【英文】专业清晰、自然流畅、符合国外阅读习惯
3. 中文 50-150 字，英文 50-120 词
4. 输出时用 ---ZH--- 和 ---EN--- 标记分隔

输出格式：

---ZH---
[中文描述]

---EN---
[英文描述]"""

def build_zh_prompt(item):
    """为中文需要重写但英文已经OK的工具生成中文描述"""
    title = item.get('title', '')
    cat = (item.get('category') or [''])[0] or 'uncategorized'
    en = item.get('abstract', '')[:300]

    return f"""你是一个专业的AI工具文案专家。请根据以下英文描述，为工具「{title}」写诙谐幽默的中文介绍。

英文原文：{en}

要求：
1. 口语化、诙谐幽默、有画面感、接地气
2. 突出核心功能，技术术语保留英文不翻译
3. 50-150 字
4. 输出格式：---ZH--- 然后换行直接输出中文描述

输出格式：

---ZH---
[中文描述]"""

def extract_texts(raw):
    """从 Ollama 返回中用分隔符提取中文和英文"""
    zh, en = None, None
    if not raw:
        return zh, en

    if '---ZH---' in raw:
        zh_part = raw.split('---ZH---')[1].split('---')[0] if raw.count('---ZH---') == 1 else raw.split('---ZH---')[1]
        if '---EN---' in zh_part:
            zh_part = zh_part.split('---EN---')[0]
        zh = zh_part.strip().strip('"').strip("'").strip('\n')
        if not zh:
            zh = None

    if '---EN---' in raw:
        parts = raw.split('---EN---')
        if len(parts) > 1:
            en_part = parts[1]
            if '---' in en_part:
                en_part = en_part.split('---')[0]
            en = en_part.strip().strip('"').strip("'").strip('\n')
            if not en:
                en = None

    # 兜底：如果没有分隔符但有内容，尝试直接提取
    if not zh and not en:
        lines = [l.strip() for l in raw.split('\n') if l.strip()]
        for line in lines:
            if len(line) > 15 and any('\u4e00' <= c <= '\u9fff' for c in line):
                zh = line
                break

    return zh, en

def main():
    print("=" * 60)
    print("   AIbounty 全量工具描述打磨 · 盘古敕令版")
    print("=" * 60)

    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    items = data['items']
    total = len(items)

    # ── 扫描 ──
    stats = {'good': 0, 'en_bad': 0, 'zh_dry': 0, 'both_bad': 0, 'both_missing': 0, 'zh_missing': 0}
    for item in items:
        cls = classify(item)
        stats[cls] = stats.get(cls, 0) + 1

    print(f"\n总计: {total}")
    print(f"  ✅ 全部达标:        {stats['good']}")
    print(f"  ⚠️  中文直译需重写:  {stats['zh_dry']}")
    print(f"  ⚠️  英文垃圾+中文直译: {stats['both_bad']}")
    print(f"  ❌ 英文垃圾:         {stats['en_bad']}")
    print(f"  ❌ 英文垃圾+中文缺失: {stats['both_missing']}")
    print(f"  ❌ 中文缺失:         {stats['zh_missing']}")

    # ── 需要修复的 ──
    fix_pool = []
    for item in items:
        cls = classify(item)
        if cls == 'good':
            continue
        fix_pool.append((cls, item))

    total_fix = len(fix_pool)
    if total_fix == 0:
        print("\n[OK] 全部达标，无需修复")
        return

    print(f"\n开始修复 {total_fix} 条...")

    success = 0
    failed = 0

    for idx, (cls, item) in enumerate(fix_pool):
        title = (item.get('title') or '')[:35]
        print(f"  [{idx+1}/{total_fix}] {title}...", end=" ", flush=True)

        if cls in ('zh_dry', 'zh_missing'):
            # 英文OK，只需重写中文
            prompt = build_zh_prompt(item)
            raw = call_ollama(prompt)
            if raw:
                zh, _ = extract_texts(raw)
                if zh and is_chinese_ok(zh):
                    item['abstract_zh'] = zh
                    success += 1
                    print(f"OK 新中文({len(zh)}字)")
                else:
                    print("FAILED 提取无效")
                    failed += 1
            else:
                print("FAILED 无响应")
                failed += 1

        elif cls in ('both_bad', 'both_missing', 'en_bad'):
            # 英文也垃圾，双重重写
            prompt = build_both_prompt(item)
            raw = call_ollama(prompt)
            has_zh, has_en = False, False
            if raw:
                zh, en = extract_texts(raw)
                if zh and is_chinese_ok(zh):
                    item['abstract_zh'] = zh
                    has_zh = True
                if zh and en and len(en) > 20:
                    item['abstract'] = en
                    has_en = True
                if has_zh or has_en:
                    success += 1
                    print(f"OK 中文({'✓' if has_zh else '✗'} {len(zh or '')}字) 英文({'✓' if has_en else '✗'} {len(en or '')}字)")
                else:
                    print("FAILED 提取无效")
                    failed += 1
            else:
                print("FAILED 无响应")
                failed += 1

        # 增量保存
        if (idx + 1) % SAVE_INTERVAL == 0:
            with open(DATA_PATH, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
            print(f"  [SAVE] 已保存 {idx+1} 条...")

        time.sleep(RATE_LIMIT)

    # 最终保存
    with open(DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, separators=(',', ':'))

    print(f"\n{'='*60}")
    print(f"   修复完成: 成功 {success}, 失败 {failed}")

    # 最终验证
    final_stats = {'good': 0, 'zh_dry': 0, 'other': 0}
    for item in items:
        cls = classify(item)
        if cls == 'good':
            final_stats['good'] += 1
        elif cls == 'zh_dry':
            final_stats['zh_dry'] += 1
        else:
            final_stats['other'] += 1

    print(f"\n最终状态:")
    print(f"  ✅ 全部达标:  {final_stats['good']}/{total}")
    print(f"  ⚠️ 仍有直译:  {final_stats['zh_dry']}/{total}")
    print(f"  ❌ 其他问题:  {final_stats['other']}/{total}")

if __name__ == '__main__':
    main()
