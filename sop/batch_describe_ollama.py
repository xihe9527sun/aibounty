#!/usr/bin/env python3
"""batch_describe_ollama.py — Ollama 批量生成描述（单条模式，保质量）
用法:
    PYTHONIOENCODING=utf-8 python batch_describe_ollama.py         # 完整运行
    PYTHONIOENCODING=utf-8 python batch_describe_ollama.py --zh    # 只补中文  
    PYTHONIOENCODING=utf-8 python batch_describe_ollama.py --en    # 只补英文
    PYTHONIOENCODING=utf-8 python batch_describe_ollama.py --check # 预览

中文：诙谐+专业，像朋友安利
英文：幽默评论，不硬译中文
"""
import json, os, sys, time, urllib.request, re, random

DATA_PATH = r"E:\ToolPilot\site\data.json"
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5:7b"

CAT_ZH = {
    "media": "创作/媒体", "agent": "AI Agent", "llm": "大模型",
    "dev-tool": "开发工具", "data-science": "数据分析",
    "rag": "知识库/RAG", "uncategorized": "AI工具",
}
SCENE_ZH = {
    "写代码": "写代码", "写文章": "写文章", "画图设计": "画图设计",
    "数据分析": "数据分析", "AI聊天": "AI对话", "做视频": "做视频", "自动化": "自动化"
}

def ollama(prompt, timeout=90):
    payload = json.dumps({
        "model": MODEL, "prompt": prompt, "stream": False,
        "options": {"temperature": 0.8, "top_p": 0.9, "max_tokens": 300}
    }).encode()
    try:
        r = urllib.request.urlopen(urllib.request.Request(OLLAMA_URL, data=payload,
            headers={"Content-Type": "application/json"}), timeout=timeout)
        text = json.loads(r.read()).get("response", "").strip().strip('"').strip("'")
        return text
    except: return ""

GEN_ZH_PROMPT = """你是在AI圈混了十年的老炮，嘴毒眼光准。给这个AI工具写一段推荐（至少50个汉字，写够再停）。

工具名称：**{name}**
分类：{cat}
场景：{scene}

要求：
- 有梗：吐槽、反讽、神比喻，不要废话开头
- 专业：点出核心优势，比竞品强在哪
- 语感：像人说的话，不是AI说明书
- 工具名用 **英文** 嵌进去
- 只输出描述，不要多余内容"""

GEN_EN_PROMPT = """You're a veteran developer who's seen every tool come and go. Your taste is sharp, your humor is dry, and you never waste words. Write a pithy recommendation (50-100 chars) for "{name}".

Category: {cat} | Scenario: {scene}

Rules:
- Be wry, sarcastic, or darkly funny — a hot take, not a product page
- Say what this tool actually excels at vs the alternatives
- Name-drop the tool as **{name}** naturally
- This is NOT a translation of any Chinese description — write it from scratch for a global audience
- 50-100 characters, tight and sharp"""

def zh_len(text):
    """统计汉字数量（不含标点、英文字母、数字）"""
    return sum(1 for c in text if '\u4e00' <= c <= '\u9fff')

def gen_one(item, lang="zh", max_retries=5):
    name = item.get("title", "?")
    repo = name.split("/")[-1] if "/" in name else name
    cats = item.get("category", []) or []
    cat = CAT_ZH.get(cats[0], "AI") if cats else "AI"
    scenes = item.get("scene", []) or []
    scene = SCENE_ZH.get(scenes[0], "") if scenes else ""
    
    best_result = ""
    best_cn = 0
    
    for attempt in range(max_retries + 1):
        if lang == "zh":
            prompt = GEN_ZH_PROMPT.format(name=repo, cat=cat, scene=scene or "效率")
        else:
            prompt = GEN_EN_PROMPT.format(name=repo, cat=cat, scene=scene or "productivity")
        
        result = ollama(prompt)
        if not result:
            continue
        
        # 中文：汉字数 50-80
        if lang == "zh":
            cn_count = zh_len(result)
            if cn_count >= 50:
                return result  # 超过50汉字就收
            if cn_count > best_cn:
                best_cn = cn_count
                best_result = result
        else:
            if len(result) >= 40:
                cn_chars = zh_len(result)
                if cn_chars <= 10:  # 英文不含中文
                    return result
                best_result = result
    
    # 全部重试完都没命中 → 返回最好的那次结果（只要达标）
    if lang == "zh" and best_cn >= 50:
        return best_result
    return ""  # 放弃，让主循环标记为失败

def main():
    check = "--check" in sys.argv
    do_zh = "--zh" in sys.argv or not sys.argv[1:] or all(a.startswith('-') for a in sys.argv[1:])
    do_en = "--en" in sys.argv or not sys.argv[1:] or all(a.startswith('-') for a in sys.argv[1:])
    
    print(f"  🤖 AIbounty · Ollama 描述生成 [{MODEL}]")
    print(f"  ═{'═'*45}")
    
    data = json.load(open(DATA_PATH, "r", encoding="utf-8"))
    items = data.get("items", [])
    
    need_zh = [] if not do_zh else []
    need_en = [] if not do_en else []
    
    for item in items:
        abs_zh = (item.get("abstract_zh") or "").strip()
        abs_en = (item.get("abstract") or "").strip()
        if do_zh and (not abs_zh or len(abs_zh) < 15):
            need_zh.append(item)
        if do_en and (not abs_en or len(abs_en) < 40):
            need_en.append(item)
    
    print(f"\n  📊 总数: {len(items)} | 缺ZH: {len(need_zh)} | 缺EN: {len(need_en)}")
    
    if check:
        if need_zh:
            print(f"\n  📝 ZH 样本 (前3):")
            for item in need_zh[:3]:
                print(f"     - {item.get('title','?')[:40]}")
        if need_en:
            print(f"\n  📝 EN 样本 (前3):")
            for item in need_en[:3]:
                print(f"     - {item.get('title','?')[:40]}")
        print(f"\n  📋 预览模式，共需生成 {len(need_zh)+len(need_en)} 条")
        return
    
    # ── 逐个生成 ──
    ok_zh = ok_en = fail_zh = fail_en = 0
    last_save = time.time()
    
    def save_progress():
        data["items"] = items
        data["updated_at"] = time.strftime('%Y-%m-%d %H:%M:%S')
        json.dump(data, open(DATA_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    
    # 先补英文（数量少，先搞定）
    if need_en:
        print(f"\n  🌍 生成英文 ({len(need_en)}条)...")
        for i, item in enumerate(need_en):
            result = gen_one(item, lang="en")
            if result and len(result) >= 20:
                item["abstract"] = result[:200]
                ok_en += 1
            else:
                fail_en += 1
            
            if (i+1) % 10 == 0 or i == 0 or i == len(need_en)-1:
                print(f"     [{i+1}/{len(need_en)}] EN: ✅{ok_en} ❌{fail_en}", flush=True)
            
            # 每20条保存一次
            if (i+1) % 20 == 0:
                save_progress()
                print(f"     💾 已保存")
    
    # 再补中文（批量大）
    if need_zh:
        print(f"\n  🌏 生成中文 ({len(need_zh)}条 预计约{len(need_zh)*8//60}分钟)...")
        for i, item in enumerate(need_zh):
            result = gen_one(item, lang="zh")
            if result and len(result) >= 10:
                item["abstract_zh"] = result[:200]
                ok_zh += 1
            else:
                fail_zh += 1
            
            if (i+1) % 10 == 0 or i == 0 or i == len(need_zh)-1 or fail_zh >= 3:
                elapsed = time.time() - last_save
                eta = (elapsed / max(i+1, 1)) * (len(need_zh) - i - 1) / 60
                print(f"     [{i+1}/{len(need_zh)}] ZH: ✅{ok_zh} ❌{fail_zh} | ETA: {eta:.0f}min", flush=True)
                fail_zh = 0
            
            if (i+1) % 20 == 0:
                save_progress()
                print(f"     💾 已保存")
    
    # ── 最终保存 ──
    save_progress()
    
    en_pct = len([i for i in items if len((i.get("abstract") or "").strip()) >= 40]) / len(items) * 100
    zh_pct = len([i for i in items if len((i.get("abstract_zh") or "").strip()) >= 15]) / len(items) * 100
    
    print(f"\n  {'═'*45}")
    print(f"  ✅ 全部完成!")
    print(f"  📊 最终健康度:")
    print(f"     EN描述(>=40字): {en_pct:.1f}%")
    print(f"     ZH描述(>=15字): {zh_pct:.1f}%")
    
    # 展示
    print(f"\n  📖 生成样本:")
    updated = need_zh + need_en
    random.seed(42)
    for s in random.sample(updated, min(6, len(updated))):
        en = (s.get('abstract') or '')[:100]
        zh = (s.get('abstract_zh') or '')[:80]
        if en: print(f"     [{s.get('title','?')[:30]}]\n       EN: {en}")
        if zh: print(f"       ZH: {zh}")
        print()

if __name__ == "__main__":
    t0 = time.time()
    main()
    print(f"  ⏱ 耗时: {(time.time()-t0)/60:.1f} 分钟")
