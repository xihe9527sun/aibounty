#!/usr/bin/env python3
"""
batch_describe.py — AIbounty 工具描述批量优化引擎 v1.0
════════════════════════════════════════════════
为所有工具生成"诙谐但专业、符合国外品味"的英文描述。
中文模式：中文主体+英文关键词混排
英文模式：纯英文

策略：
  1. 工具标题 → 提取关键词（主名+副名）
  2. 分类 → 选择对应的角度和语气
  3. 场景 → 加入场景化推荐
  4. 多种模板 + 随机变异 → 避免千篇一律
"""
import json, random, os, re
from datetime import datetime

DATA_PATH = r"E:\ToolPilot\site\data.json"

# ── 语气词库（让描述有"人味儿"） ──
OPENERS_EN = [
    "Meet", "Say hello to", "Introducing", "Check out",
    "Ever wished for", "Here's", "If you're looking for",
    "Tired of switching tools? Try",
    "The smart way to",
    "Your new go-to for"
]
OPENERS_ZH = [
    "认识一下", "来看看", "强烈推荐", "别找了，就是它——",
    "想效率翻倍？试试", "自从用了", "每一个",
    "不只是又一个", "终于有了一个能帮你"
]

PUNCHLINES = [
    "and it actually works.",
    "because your time is worth it.",
    "and thank us later.",
    "because mediocre tools are so 2024.",
    "and watch your productivity soar.",
    "because you deserve better.",
    "the AI way.",
    "no PhD required.",
    "and yes, it's as cool as it sounds.",
    "because who has time for complicated?",
]

# ── 分类→角度的映射 ──
CAT_ANGLES = {
    "agent": {
        "tagline": "autonomous AI agent",
        "hook": ["delegating tasks to AI", "building autonomous workflows", "letting AI handle the grunt work"],
        "zh_tag": "自主AI智能体",
    },
    "llm": {
        "tagline": "large language model",
        "hook": ["talking to AI that actually understands", "harnessing the power of LLMs", "getting intelligent text generation"],
        "zh_tag": "大语言模型",
    },
    "rag": {
        "tagline": "retrieval-augmented generation",
        "hook": ["connecting AI to your own data", "building knowledge-aware chatbots", "making AI actually useful with your docs"],
        "zh_tag": "RAG知识增强",
    },
    "dev-tool": {
        "tagline": "developer tool",
        "hook": ["shipping code faster", "debugging without the headache", "streamlining your dev workflow"],
        "zh_tag": "开发工具",
    },
    "media": {
        "tagline": "media & design tool",
        "hook": ["creating stunning visuals", "editing like a pro", "turning ideas into images"],
        "zh_tag": "媒体创作",
    },
    "data-science": {
        "tagline": "data science tool",
        "hook": ["crunching numbers at scale", "finding insights in your data", "making data-driven decisions"],
        "zh_tag": "数据科学",
    },
    "AI视频": {
        "tagline": "AI video generation",
        "hook": ["generating videos from text prompts", "creating studio-quality video content", "turning scripts into videos"],
        "zh_tag": "AI视频生成",
    },
    "AI": {
        "tagline": "AI-powered tool",
        "hook": ["getting AI to do the heavy lifting", "supercharging your workflow with AI"],
        "zh_tag": "AI工具",
    },
    "uncategorized": {
        "tagline": "AI tool",
        "hook": ["discovering what AI can do for you", "exploring the cutting edge of AI"],
        "zh_tag": "AI工具",
    },
}

# ── 场景短语 ──
SCENE_TAGS = {
    "写代码": ("writing code", "coding", "development", "写代码/编程"),
    "写文章": ("writing articles", "content creation", "blogging", "写作/内容创作"),
    "画图设计": ("designing visuals", "graphic design", "creating art", "视觉设计/创作"),
    "做视频": ("video production", "video editing", "creating videos", "视频制作/编辑"),
    "数据分析": ("data analysis", "analytics", "data science", "数据分析/挖掘"),
    "AI聊天": ("AI chat", "conversational AI", "chatbots", "AI对话/聊天"),
    "自动化": ("automation", "workflow automation", "automating tasks", "自动化工作流"),
}

# ── GitHub项目专用 ──
def extract_repo_name(title):
    """从 'owner/repo' 格式提取仓库名"""
    if "/" in title:
        parts = title.split("/")
        if len(parts) == 2 and not parts[0].startswith("http"):
            return parts[1], parts[0]
    return title, None

def generate_en(item):
    """生成英文描述"""
    title = item.get("title", "")
    cats = item.get("category", [])
    scenes = item.get("scene", [])
    source = item.get("source", "")
    score = item.get("score", 0)
    try: score_num = int(score) if score else 0
    except: score_num = 0

    # 提取关键信息
    repo_name, owner = extract_repo_name(title)
    primary_cat = cats[0] if cats else "uncategorized"
    angle = CAT_ANGLES.get(primary_cat, CAT_ANGLES["uncategorized"])

    # 如果已经有不错的描述，保留
    existing = (item.get("abstract") or "").strip()
    if len(existing) > 50 and not existing.startswith(title[:20]):
        return existing

    # 开始构建
    opener = random.choice(OPENERS_EN)
    hook = random.choice(angle["hook"])
    punch = random.choice(PUNCHLINES)
    scene_tag = random.choice(SCENE_TAGS[scenes[0]]) if scenes else ""

    # 仓库名友好化
    display_name = repo_name or title
    if repo_name and repo_name != title:
        display_name = f"**{repo_name}** ({owner})"
    else:
        display_name = f"**{title}**"

    # 构建句子
    parts = [f"{opener} {display_name} — ", ""]

    if scenes and scene_tag:
        parts[1] += f"perfect for {scene_tag}. "
    elif cats and primary_cat != "uncategorized":
        parts[1] += f"a {angle['tagline']} that makes {hook} a breeze. "

    # 补充功能描述
    if repo_name and repo_name != title:
        # 开源项目
        star_tag = f" ⭐ {score_num/1000:.1f}k stars" if score_num >= 1000 else ""
        parts[1] += f"Open-source{star_tag}, built by {owner or 'the community'}, {punch}"
    else:
        # 普通工具
        parts[1] += f"Built for {', '.join(scenes) if scenes else 'getting things done'}"

    return "".join(parts)

def generate_zh(item):
    """生成中文描述（中英混合）"""
    title = item.get("title", "")
    cats = item.get("category", [])
    scenes = item.get("scene", [])
    source = item.get("source", "")

    # 如果已有中文描述且不错，保留
    existing_zh = (item.get("abstract_zh") or "").strip()
    if len(existing_zh) > 15 and not existing_zh.isascii():
        return existing_zh

    # 用英文生成器先生成英文，再融入中文
    repo_name, owner = extract_repo_name(title)
    primary_cat = cats[0] if cats else "uncategorized"
    angle = CAT_ANGLES.get(primary_cat, CAT_ANGLES["uncategorized"])
    scene_tag_zh = random.choice(SCENE_TAGS[scenes[0]][3:]) if scenes else ""

    opener = random.choice(OPENERS_ZH)
    display = repo_name or title

    # 核心英文术语保留
    eng_terms = angle["tagline"]
    hook_en = random.choice(angle["hook"])

    # 中英混合
    if scene_tag_zh:
        text = f"{opener} **{display}**——{scene_tag_zh}场景下的{eng_terms}神器，帮你{hook_en}。"
    else:
        text = f"{opener} **{display}**——这款{eng_terms}能帮你{hook_en}，效率直接拉满。"

    # 偶尔加个emoji
    if random.random() < 0.3:
        emojis = {"agent":"🤖","llm":"🧠","rag":"🔗","dev-tool":"🛠","data-science":"📊","media":"🎨","AI视频":"🎬","AI":"✨"}
        text = f"{emojis.get(primary_cat,'')} {text}"

    return text

def main():
    print("  ⚡ AIbounty 描述优化引擎启动\n")

    data = json.load(open(DATA_PATH, "r", encoding="utf-8"))
    items = data.get("items", data.get("tools", []))
    total = len(items)

    updated_en = 0
    updated_zh = 0

    for i, item in enumerate(items):
        old_en = (item.get("abstract") or "").strip()
        old_zh = (item.get("abstract_zh") or "").strip()

        # 生成新英文描述
        new_en = generate_en(item)
        if new_en != old_en:
            item["abstract"] = new_en
            updated_en += 1

        # 生成新中文描述
        new_zh = generate_zh(item)
        if new_zh != old_zh:
            item["abstract_zh"] = new_zh
            updated_zh += 1

        if (i+1) % 100 == 0:
            print(f"  [{i+1}/{total}] 已处理...")

    # 保存
    if "items" in data:
        data["items"] = items
    else:
        data["tools"] = items

    json.dump(data, open(DATA_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    print(f"\n  ✅ 处理完成")
    print(f"  📝 英文描述更新: {updated_en}/{total}")
    print(f"  📝 中文描述更新: {updated_zh}/{total}")
    print(f"  💾 已保存到 {DATA_PATH}")

    # 展示几个例子
    print(f"\n  📖 示例:")
    for item in items[:3]:
        print(f"  [{item['title']}]")
        print(f"    EN: {(item.get('abstract') or '')[:100]}")
        print(f"    ZH: {(item.get('abstract_zh') or '')[:60]}")
        print()

if __name__ == "__main__":
    main()
