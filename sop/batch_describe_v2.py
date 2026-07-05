#!/usr/bin/env python3
"""
batch_describe_v2.py — AIbounty 描述优化 v2
═══════════════════════════════════════
更丰富的模板、更自然的语言、更好的中英混合。
"""
import json, os, random, re

DATA_PATH = r"E:\ToolPilot\site\data.json"

# ═══════════════════════════════════════
# 英文描述生成
# ═══════════════════════════════════════

EN_PATTERNS = [
    lambda t, cats, scs, src, sc: (
        t["disp"] + " — " + _join(scs["en"]) + " meets AI. "
        + _pick(["It just works.", "No PhD required.", "Setup takes minutes, results last forever.", "Your future self will thank you."])
    ),
    lambda t, cats, scs, src, sc: (
        "Remember when " + _pick(scs["en_hooks"]) + " was a pain? "
        + t["disp"] + " fixes that. " + _pick(["It's that simple.", "And it's surprisingly good.", "You'll wonder how you lived without it."])
    ),
    lambda t, cats, scs, src, sc: (
        _pick(["Built for", "Designed for", "Made for"]) + " " + _join(scs["en"]) + ". "
        + t["disp"] + " " + _pick(["handles the heavy lifting so you don't have to.", "turns hours of work into minutes.", "is the AI co-pilot you didn't know you needed."])
    ),
    lambda t, cats, scs, src, sc: (
        t["disp"] + ". " + _pick(["Your go-to AI sidekick.", "AI-powered, human-approved.", "The tool that actually delivers.", "Because good enough is never enough."])
    ),
    lambda t, cats, scs, src, sc: (
        _pick(["Need to", "Trying to", "Looking to"]) + " " + _pick(scs["en_verbs"]) + "? "
        + t["disp"] + " " + _pick(["has your back.", "is exactly what you need.", "does it better than anything else."])
    ),
    lambda t, cats, scs, src, sc: (
        _pick(["Most tools are overpriced and underwhelming.", "Let's be honest: most tools in this space are meh.", "It doesn't have to be this complicated."])
        + " " + t["disp"] + " " + _pick(["changes that.", "is different.", "actually gets it right."])
    ),
]

def _pick(lst):
    return random.choice(lst) if lst else ""

def _join(lst):
    return lst[0] if len(lst) == 1 else ", ".join(lst[:-1]) + " and " + lst[-1]

def get_scene_tags(scenes):
    """从场景列表生成英文短语"""
    if not scenes:
        return {
            "en": ["getting things done"],
            "en_single": ["workflow"],
            "en_hooks": ["getting things done"],
            "en_verbs": ["get more done"]
        }
    
    scene_map = {
        "写代码":   {"en":["coding","software development"], "en_single":["coding","development"], "en_hooks":["writing code"], "en_verbs":["write better code","ship features faster"]},
        "写文章":   {"en":["writing","content creation"], "en_single":["writing"], "en_hooks":["producing content"], "en_verbs":["write better content","create engaging articles"]},
        "画图设计": {"en":["design","visual creation"], "en_single":["design work"], "en_hooks":["creating visuals"], "en_verbs":["design stunning visuals","create beautiful graphics"]},
        "做视频":   {"en":["video production","video creation"], "en_single":["video work"], "en_hooks":["editing videos"], "en_verbs":["produce professional videos","edit videos like a pro"]},
        "数据分析": {"en":["data analysis","analytics"], "en_single":["data work"], "en_hooks":["crunching numbers"], "en_verbs":["analyze data faster","extract insights from data"]},
        "AI聊天":   {"en":["AI chat","conversational AI"], "en_single":["chat"], "en_hooks":["building chatbots"], "en_verbs":["build smarter chatbots","create engaging AI conversations"]},
        "自动化":   {"en":["automation","workflow automation"], "en_single":["automation"], "en_hooks":["automating workflows"], "en_verbs":["automate repetitive tasks","streamline your workflows"]},
    }
    
    result = {"en":[],"en_single":[],"en_hooks":[],"en_verbs":[]}
    for s in scenes:
        if s in scene_map:
            for k in result:
                result[k].extend(scene_map[s].get(k,[]))
    
    for k in result:
        if not result[k]:
            result[k] = ["getting things done" if k != "en_verbs" else "get things done"]
    
    return result

def get_cat_tag(cats):
    if not cats or "uncategorized" in cats:
        return "AI tool"
    labels = {
        "agent": "AI agent", "llm": "language model", "rag": "RAG tool",
        "dev-tool": "dev tool", "media": "creative tool", "data-science": "analytics tool",
        "AI视频": "video AI", "AI": "AI tool"
    }
    return labels.get(cats[0], "AI tool")

def extract_info(item):
    title = item.get("title","")
    repo_name = None
    if "/" in title and not title.startswith("http"):
        parts = title.split("/")
        if len(parts) == 2:
            repo_name, owner = parts
    if repo_name:
        display = f"**{repo_name}**"
        star = ""
        try: sc = int(item.get("score",0)) if item.get("score") else 0
        except: sc = 0
        if sc >= 5000: star = f" ({sc//1000}k stars)"
        elif sc >= 1000: star = f" ({sc//1000}.{sc%1000//100}k stars)"
        display += star
    else:
        display = f"**{title}**"
    return {
        "name": repo_name or title,
        "disp": display,
        "owner": owner if repo_name else None,
    }

def gen_en(item):
    old = (item.get("abstract") or "").strip()
    # 保留好的旧描述
    if len(old) > 50 and not old.startswith("Abstract") and not old.startswith(item.get("title","")[:20]):
        return old
    
    t = extract_info(item)
    cats = item.get("category",[])
    scenes = item.get("scene",[])
    sc_tags = get_scene_tags(scenes)
    
    pattern = random.choice(EN_PATTERNS)
    return pattern(t, cats, sc_tags, item.get("source",""), item.get("score",0))

# ═══════════════════════════════════════
# 中文描述生成（中英自然混合）
# ═══════════════════════════════════════

ZH_PATTERNS = [
    lambda t, cats, scs: (
        "一款面向" + _pick(scs["zh"]) + "场景的" + _pick(cats) + "。" + t["disp"] + "帮你" + _pick(scs["zh_verbs"]) + "，"
        + _pick(["效率直接翻倍。", "省心又省力。", "用过就回不去了。", "谁用谁知道。"])
    ),
    lambda t, cats, scs: (
        "写代码、做设计、搞分析——" + t["disp"] + "都能插上手。" + _pick(cats) + "加持，" + _pick(scs["zh_verbs"]) + "不再是难题。"
    ),
    lambda t, cats, scs: (
        t["disp"] + "——AI 时代的" + _pick(cats) + "利器。"
        + _pick(["上手快、效果好。", "效率直接拉满。", "用了就离不开了。"])
    ),
    lambda t, cats, scs: (
        "还在为" + _pick(scs["zh_hooks"]) + "发愁？" + t["disp"] + "来救场了。"
        + _pick(cats) + " + " + _pick(scs["zh_single"]) + "，" + _pick(["效率拉满。", "轻松搞定。", "省下来的时间去喝咖啡。"])
    ),
]

ZH_CAT = {
    "agent": ["AI Agent", "智能体", "自主AI"],
    "llm": ["LLM", "大语言模型"],
    "rag": ["RAG", "知识检索增强"],
    "dev-tool": ["开发工具", "DevTool"],
    "media": ["创作工具", "创意AI"],
    "data-science": ["数据分析", "数据科学工具"],
    "AI视频": ["AI视频", "视频生成"],
    "AI": ["AI工具"],
    "uncategorized": ["AI工具"],
}

ZH_SCENE = {
    "写代码": {"zh":["编程","开发","写代码"], "zh_single":["写代码","开发"], "zh_hooks":["调Bug","写代码"], "zh_verbs":["提高开发效率","快速出活"]},
    "写文章": {"zh":["写作","内容创作"], "zh_single":["写作"], "zh_hooks":["憋文章","写文案"], "zh_verbs":["高效产出内容","写出好文章"]},
    "画图设计": {"zh":["设计","视觉创作"], "zh_single":["设计"], "zh_hooks":["画图","做设计"], "zh_verbs":["快速出图","做出好设计"]},
    "做视频": {"zh":["视频制作","做视频"], "zh_single":["做视频"], "zh_hooks":["剪片子","做视频"], "zh_verbs":["高效做视频","出片如流水"]},
    "数据分析": {"zh":["数据分析","数据挖掘"], "zh_single":["数据分析"], "zh_hooks":["处理数据","做报表"], "zh_verbs":["快速分析数据","发现洞察"]},
    "AI聊天": {"zh":["AI对话","聊天"], "zh_single":["聊天"], "zh_hooks":["做客服","搭对话"], "zh_verbs":["搭好对话系统","搞定AI聊天"]},
    "自动化": {"zh":["自动化","工作流"], "zh_single":["自动化"], "zh_hooks":["重复劳动","手动流程"], "zh_verbs":["自动化工作流","解放双手"]},
}

def gen_zh(item):
    old = (item.get("abstract_zh") or "").strip()
    if len(old) > 15 and not old.isascii():
        return old
    
    title = item.get("title","")
    t = extract_info(item)
    cats_raw = item.get("category",[]) or ["uncategorized"]
    scenes_raw = item.get("scene",[]) or []
    
    # 分类标签
    cat_tags = []
    for c in cats_raw:
        if c in ZH_CAT:
            cat_tags.extend(ZH_CAT[c])
    if not cat_tags:
        cat_tags = ["AI工具"]
    
    # 场景标签
    sc_tags = {"zh":["通用"], "zh_single":["效率"], "zh_hooks":["效率"], "zh_verbs":["提高效率"]}
    for s in scenes_raw:
        if s in ZH_SCENE:
            for k in sc_tags:
                v = ZH_SCENE[s].get(k,[])
                if v: sc_tags[k].extend(v)
    for k in sc_tags:
        if not sc_tags[k]:
            sc_tags[k] = ["效率"]
    
    pattern = random.choice(ZH_PATTERNS)
    try:
        return pattern(t, cat_tags, sc_tags)
    except:
        return f"{t['disp']}——AI 时代的{_pick(cat_tags)}利器，帮你{_pick(sc_tags['zh_verbs'])}。"

def _pick(lst):
    return random.choice(lst) if lst else ""

# ═══════════════════════════════════════
# 主流程
# ═══════════════════════════════════════

def main():
    print("  ⚡ AIbounty 描述优化引擎 v2\n")
    data = json.load(open(DATA_PATH, "r", encoding="utf-8"))
    items = data.get("items", data.get("tools", []))
    total = len(items)
    
    upd_en = upd_zh = 0
    
    for i, item in enumerate(items):
        old_en = (item.get("abstract") or "").strip()
        old_zh = (item.get("abstract_zh") or "").strip()
        
        new_en = gen_en(item)
        if new_en != old_en:
            item["abstract"] = new_en
            upd_en += 1
        
        new_zh = gen_zh(item)
        if new_zh != old_zh:
            item["abstract_zh"] = new_zh
            upd_zh += 1
        
        if (i+1) % 200 == 0:
            print(f"  [{i+1}/{total}] EN更新:{upd_en} ZH更新:{upd_zh}")
    
    if "items" in data: data["items"] = items
    json.dump(data, open(DATA_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    
    print(f"\n  ✅ 完成: EN更新{upd_en}/{total} ZH更新{upd_zh}/{total}")
    
    # 展示样本
    random.seed(123)
    for s in random.sample(items, 5):
        print(f"\n  [{s['title']}]")
        print(f"    EN: {(s.get('abstract') or '')[:120]}")
        print(f"    ZH: {(s.get('abstract_zh') or '')[:80]}")

if __name__ == "__main__":
    main()
