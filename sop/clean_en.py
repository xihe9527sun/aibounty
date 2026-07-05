#!/usr/bin/env python3
"""clean_en.py — 清洗EN描述中的中文内容，重新生成英文幽默评语"""
import json, sys, time, urllib.request, re

DATA_PATH = r"E:\ToolPilot\site\data.json"
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5:7b"

EN_PROMPT = """You're a veteran developer with dry wit. Write a sharp recommendation (50-100 chars) for "{name}".

Rules:
- Be wry, sarcastic, or darkly funny — a hot take, not a product page
- Say what this tool actually excels at vs alternatives
- NOT a translation from Chinese. Write from scratch for a global audience.
- Name-drop the tool as **{name}** naturally
- 50-100 characters exactly"""

def ollama(prompt, timeout=90):
    payload = json.dumps({
        "model": MODEL, "prompt": prompt, "stream": False,
        "options": {"temperature": 0.8, "top_p": 0.9, "max_tokens": 200}
    }).encode()
    try:
        r = urllib.request.urlopen(urllib.request.Request(OLLAMA_URL, data=payload,
            headers={"Content-Type": "application/json"}), timeout=timeout)
        return json.loads(r.read()).get("response","").strip().strip('"').strip("'")
    except: return ""

def zh_len(text):
    return sum(1 for c in text if '\u4e00' <= c <= '\u9fff')

data = json.load(open(DATA_PATH, "r", encoding="utf-8"))
items = data.get("items", [])

# 找EN含中文的
need = [i for i in items if zh_len(i.get("abstract","") or "") >= 15]
print(f"  📊 EN含中文需清洗: {len(need)} 条")

ok = 0
for idx, item in enumerate(need):
    title = item.get("title","?")
    repo = title.split("/")[-1] if "/" in title else title
    
    for retry in range(3):
        prompt = EN_PROMPT.format(name=repo)
        result = ollama(prompt)
        if result:
            # 检查是否还有中文
            if zh_len(result) < 10 and len(result) >= 30:
                item["abstract"] = result[:300]
                ok += 1
                break
    
    if (idx + 1) % 10 == 0 or idx == len(need) - 1:
        print(f"     [{idx+1}/{len(need)}] ✅{ok} ❌{idx+1-ok}", flush=True)
    
    if (idx + 1) % 30 == 0:
        json.dump(data, open(DATA_PATH,"w",encoding="utf-8"), ensure_ascii=False, indent=2)
        print(f"     💾 已保存 ({idx+1})")

# 最终保存
json.dump(data, open(DATA_PATH,"w",encoding="utf-8"), ensure_ascii=False, indent=2)

en_pct = len([i for i in items if zh_len(i.get("abstract","") or "") < 15]) / len(items) * 100
print(f"\n  ✅ 完成! EN清洗后覆盖率: {en_pct:.1f}%")
