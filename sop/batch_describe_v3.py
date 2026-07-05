#!/usr/bin/env python3
"""batch_describe_v3.py — 最终版：清除所有模板残留，全量重生成
"""
import json, os, random, re

DATA_PATH = r"E:\ToolPilot\site\data.json"

def is_template_generated(text):
    """检测是否是模板生成的垃圾描述"""
    triggers = [
        "Built for getting things done",
        "Tired of switching tools",
        "The smart way to",
        "Your new go-to for",
        "Ever wished for",
        "Say hello to",
        "If you're looking for",
        "Meet **",
        "Introducing **",
        "Check out **",
        "效率直接拉满",
        "帮你discovering",
        "帮你exploring",
        "每一个 **",
        "自从用了 **",
        "终于有了一个能帮你",
        "别找了，就是它",
        "来看看 **",
        "——这款AI tool",
        "——这款large language model",
        "——写代码/编程场景下的",
    ]
    for t in triggers:
        if t in text:
            return True
    return False

def is_good_description(text, min_len=40):
    """判断是否是真正的好描述（不是模板、不是乱码）"""
    if not text or len(text) < min_len:
        return False
    if is_template_generated(text):
        return False
    # 排除以 Abstract 开头的垃圾
    if text.startswith("Abstract") or text.startswith("abstract"):
        return False
    # 排除明显是 README 头部的
    if text.startswith("You can start editing") or text.startswith("This is a"):
        return False
    return True

# ═══════════════════════════════════════
# 英文描述
# ═══════════════════════════════════════

TEMPLATES_EN = [
    # T0: 问句 + 推荐
    lambda t, sc: f"Need a hand with {sc}? {t} does the heavy lifting so you don't have to.",
    # T1: 场景 + 工具
    lambda t, sc: f"Your AI co-pilot for {sc}. {t} — because your time is worth it.",
    # T2: 俏皮推荐
    lambda t, sc: f"Remember when {sc} was a chore? {t} remembers, and fixed it. No cape required.",
    # T3: 对比式
    lambda t, sc: f"Most {sc} tools are either overpriced or overhyped. {t} is neither. It just works.",
    # T4: 功能导向
    lambda t, sc: f"Built from the ground up for {sc}. {t} turns hours of grinding into minutes of clicking.",
    # T5: 简短有力
    lambda t, sc: f"{t}. {sc} on autopilot. You're welcome.",
    # T6: 价值主张
    lambda t, sc: f"If {sc} is part of your daily grind, {t} is about to become your new best friend.",
    # T7: 具体场景
    lambda t, sc: f"Whether you're into {sc} or just getting started, {t} meets you where you are.",
    # T8: 幽默
    lambda t, sc: f"Warning: using {t} for {sc} may cause uncontrollable productivity. Side effects include free time.",
    # T9: 结果导向
    lambda t, sc: f"Stop wrestling with {sc}. Start using {t}. Results speak for themselves.",
    # T10: 效率
    lambda t, sc: f"{t} makes {sc} so easy, you'll have time to wonder why you didn't try it sooner.",
    # T11: 探索
    lambda t, sc: f"Ready to rethink {sc}? {t} is the AI-powered answer you've been looking for.",
]

def pick(arr): return random.choice(arr)

def describe_en(item):
    title = item.get("title","")
    repo = title.split("/")[-1] if "/" in title and not title.startswith("http") else title
    cats = item.get("category",[]) or []
    scenes = item.get("scene",[]) or []
    
    # 场景短语
    scene_phrases = []
    for s in scenes:
        m = {"写代码":"coding","写文章":"writing","画图设计":"design","做视频":"video creation","数据分析":"data analysis","AI聊天":"AI chat","自动化":"automation"}
        if s in m: scene_phrases.append(m[s])
    sc = pick(scene_phrases) if scene_phrases else "getting things done"
    
    # 工具显示名
    star = ""
    try: sc_int = int(item.get("score",0)) if item.get("score") else 0
    except: sc_int = 0
    if sc_int >= 5000: star = f" ({sc_int//1000}k⭐)"
    elif sc_int >= 1000: star = f" ({sc_int//1000}k⭐)"
    
    display = f"**{repo}**{star}"
    
    tmpl = pick(TEMPLATES_EN)
    return tmpl(display, sc)

# ═══════════════════════════════════════
# 中文描述（中英混合）
# ═══════════════════════════════════════

TEMPLATES_ZH = [
    lambda t, sc, ct: f"还在为{sc}头疼？{t} 这款{ct}能帮你搞定。效率翻倍，心情也好了。",
    lambda t, sc, ct: f"写代码、做设计、搞分析——{t} 都擅长。{ct}加持，{sc}不再是难题。",
    lambda t, sc, ct: f"{t}——专为{sc}场景打造的{ct}。省心、省力、省时间。",
    lambda t, sc, ct: f"{sc}太费时间？试试 {t}。{ct}帮你自动处理，你只管喝咖啡。",
    lambda t, sc, ct: f"每一个做{sc}的人都该试试 {t}。{ct}加持，效果拔群。",
    lambda t, sc, ct: f"{t} 是一款面向{sc}场景的{ct}。不是花架子，是真能干活的那种。",
    lambda t, sc, ct: f"如果{sc}是你日常工作的一部分，{t} 这款{ct}能让你早点下班。",
]

CAT_ZH = {"agent":"AI Agent","llm":"大模型","rag":"RAG知识增强","dev-tool":"开发神器","media":"创作工具","data-science":"数据分析工具","AI视频":"AI视频工具","AI":"AI工具"}
SCENE_ZH = {"写代码":"coding/编程","写文章":"写作/内容创作","画图设计":"设计/绘图","做视频":"视频制作","数据分析":"数据分析","AI聊天":"AI对话","自动化":"自动化工作流"}

def describe_zh(item):
    cats = item.get("category",[]) or []
    scenes = item.get("scene",[]) or []
    title = item.get("title","")
    repo = title.split("/")[-1] if "/" in title and not title.startswith("http") else title
    
    ct = pick([CAT_ZH.get(c,"AI工具") for c in cats]) if cats else "AI工具"
    sc = pick([SCENE_ZH.get(s,"效率") for s in scenes]) if scenes else "效率"
    tmpl = pick(TEMPLATES_ZH)
    return tmpl(f"**{repo}**", sc, ct)

# ═══════════════════════════════════════
# 主流程
# ═══════════════════════════════════════

def main():
    print("  ⚡ AIbounty 描述优化 v3 · 全量重生成\n")
    data = json.load(open(DATA_PATH, "r", encoding="utf-8"))
    items = data.get("items", data.get("tools", []))
    total = len(items)
    
    kept_en = kept_zh = 0
    new_en = new_zh = 0
    
    for i, item in enumerate(items):
        old_en = (item.get("abstract") or "").strip()
        old_zh = (item.get("abstract_zh") or "").strip()
        
        # 英文：只保留真正的好描述
        if is_good_description(old_en):
            kept_en += 1
        else:
            item["abstract"] = describe_en(item)
            new_en += 1
        
        # 中文：只保留真正的好描述
        if is_good_description(old_zh, min_len=20):
            kept_zh += 1
        else:
            item["abstract_zh"] = describe_zh(item)
            new_zh += 1
        
        if (i+1) % 300 == 0:
            print(f"  [{i+1}/{total}] EN新:{new_en} 保留:{kept_en} | ZH新:{new_zh} 保留:{kept_zh}")
    
    if "items" in data: data["items"] = items
    json.dump(data, open(DATA_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    
    print(f"\n  ✅ 完成")
    print(f"  📝 英文: 新生成{new_en} 保留{kept_en} / 总计{total}")
    print(f"  📝 中文: 新生成{new_zh} 保留{kept_zh} / 总计{total}")
    
    # 展示
    random.seed(42)
    print("\n  📖 样本：")
    for s in random.sample(items, 6):
        print(f"  [{s['title']}]")
        print(f"    EN: {(s.get('abstract') or '')[:120]}")
        print(f"    ZH: {(s.get('abstract_zh') or '')[:80]}")
        print()

if __name__ == "__main__":
    main()
