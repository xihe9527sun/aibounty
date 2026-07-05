#!/usr/bin/env python3
"""AIbounty data.json 瘦身脚本
- 移除冗余字段 (region, grade) — 1882/1884 条重复
- 清空 262 条英文 abstract_zh，让前端用 abstract 兜底
- 修复 grade_label 乱码（UTF-8 双重编码修复）
- JSON 压缩（去缩进）
"""
import json, re, os, sys

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "site", "data.json")

# ── grade_label 修复映射 ──
GRADE_LABEL_FIX = {
    "A+": "🏆·精选",
    "A": "⭐·推荐",
    "B": "📌·关注",
}

def fix_grade_label(val):
    """修复 grade_label 乱码。如果是合法中文则保留，否则从 grade 映射。"""
    if not val:
        return val
    # 如果有合法中文（含 emoji），说明没乱码
    cn = len(re.findall(r'[\u4e00-\u9fff\U0001F300-\U0001FFFF]', val))
    if cn >= 2:
        return val
    return None  # 标记待修复

def is_english_zh(zh):
    """判断 abstract_zh 是否实际上还是英文（翻译未完成）"""
    if not zh or len(zh) < 10:
        return True
    cn = len(re.findall(r'[\u4e00-\u9fff]', zh))
    return cn < 3

def main():
    print("[INFO] 读取 data.json ...")
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    items = data['items']
    original_size = os.path.getsize(DATA_PATH)
    print(f"[INFO] 原始文件: {original_size/1024:.0f} KB, {len(items)} 条")

    # ── 1. 清理字段 ──
    removed_region = 0
    removed_grade = 0
    cleared_zh = 0
    fixed_labels = 0

    for item in items:
        # 移除 region（大量重复值）
        if 'region' in item:
            del item['region']
            removed_region += 1

        # 移除 grade（只有 3 个唯一值）
        if 'grade' in item:
            del item['grade']
            removed_grade += 1

        # 清空英文 abstract_zh（让前端兜底）
        zh = item.get('abstract_zh', '')
        if zh and is_english_zh(zh):
            item['abstract_zh'] = ""
            cleared_zh += 1

        # 修复 grade_label 乱码
        label = item.get('grade_label')
        if label:
            fixed = fix_grade_label(label)
            if fixed is None:
                grade_val = item.get('grade', 'B')
                item['grade_label'] = GRADE_LABEL_FIX.get(grade_val, '📌·关注')
                fixed_labels += 1
            elif fixed != label:
                item['grade_label'] = fixed
                fixed_labels += 1

    # ── 2. 压缩 JSON（去除缩进） ──
    minified = json.dumps(data, ensure_ascii=False, separators=(',', ':'))

    # ── 3. 写入 ──
    with open(DATA_PATH, 'w', encoding='utf-8') as f:
        f.write(minified)

    new_size = os.path.getsize(DATA_PATH)
    saved = original_size - new_size
    print(f"[OK] 压缩后: {new_size/1024:.0f} KB (-{saved/1024:.0f} KB, {saved/original_size*100:.0f}%)")
    print(f"[OK] 移除 region: {removed_region} 条")
    print(f"[OK] 移除 grade: {removed_grade} 条")
    print(f"[OK] 清空英文 abstract_zh: {cleared_zh} 条")
    print(f"[OK] 修复 grade_label: {fixed_labels} 条")

    # ── 4. 验证 JSON 合法性 ──
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        data2 = json.load(f)
    print(f"[OK] 验证通过: {len(data2['items'])} 条")
    return True

if __name__ == '__main__':
    main()
