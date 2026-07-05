#!/usr/bin/env python3
"""批量修复缺失的 abstract_zh 中文翻译
读取 data.json，找出 abstract_zh 为空/英文的工具，
用 Ollama qwen2.5:7b 翻译 abstract 并写入。
"""
import json, os, re, sys, requests, time

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "site", "data.json")
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5:7b"
BATCH_SIZE = 3      # 并发批次
RATE_LIMIT = 0.5     # 每个请求间隔

def is_chinese(text):
    if not text: return False
    cn = len(re.findall(r'[\u4e00-\u9fff]', text))
    return cn >= 3 and cn >= len(text) * 0.15

def needs_translation(item):
    zh = item.get('abstract_zh', '')
    if zh and is_chinese(zh):
        return False  # 已经有中文了
    abs_text = item.get('abstract', '')
    if not abs_text or len(abs_text) < 10:
        return False  # 没有原文可翻
    return True

def translate(text, retries=2):
    """调用 Ollama 翻译"""
    prompt = "把以下英文工具描述翻译成简洁的中文，保持技术术语不翻译，不要加任何前缀后缀，直接输出翻译结果：\n\n" + text
    for attempt in range(retries):
        try:
            resp = requests.post(OLLAMA_URL, json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.3, "num_predict": 400}
            }, timeout=60)
            if resp.status_code == 200:
                result = resp.json()
                translated = (result.get("response") or "").strip()
                if translated and is_chinese(translated):
                    return translated
            print(f"  [WARN] 第{attempt+1}次翻译结果无效: {resp.status_code}")
        except Exception as e:
            print(f"  [WARN] 第{attempt+1}次请求失败: {e}")
            time.sleep(1)
    return None

def main():
    print(f"[INFO] 读取 {DATA_PATH}")
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    items = data['items']
    to_fix = [i for i in items if needs_translation(i)]
    total = len(to_fix)

    if total == 0:
        print("[OK] 所有工具已有中文描述，无需修复")
        return

    print(f"[INFO] 需要翻译: {total} 个工具")
    print(f"[INFO] 使用模型: {MODEL}")

    success = 0
    failed = 0

    for idx, item in enumerate(to_fix):
        abs_text = item.get('abstract', '')
        title = item.get('title', '')[:40]

        # 非英文原文跳过长文本
        if not abs_text or len(abs_text) > 1200:
            print(f"  [{idx+1}/{total}] SKIP: {title} (原文过长或为空: {len(abs_text or '')}字符)")
            continue

        print(f"  [{idx+1}/{total}] 翻译: {title} ({len(abs_text)}字符)...", end=" ", flush=True)
        translated = translate(abs_text)

        if translated:
            item['abstract_zh'] = translated
            success += 1
            print(f"OK ({len(translated)}字符)", flush=True)
        else:
            # 保留英文原文占位，不删
            print("FAILED", flush=True)
            failed += 1

        # 每 20 条增量保存，防止崩溃丢失
        if success % 20 == 0 and success > 0:
            with open(DATA_PATH, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
            print(f"  [SAVE] 已保存 {success} 条...")

        time.sleep(RATE_LIMIT)

    # 最终保存
    with open(DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
    print(f"\n[OK] 最终保存: 翻译 {success}, 失败 {failed}")

if __name__ == '__main__':
    main()
