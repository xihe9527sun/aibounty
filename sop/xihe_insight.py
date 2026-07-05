#!/usr/bin/env python3
"""曦和洞察引擎 v1 — 为工具生成有温度、有观点、引人入胜的推荐语
混合方案 C：精选自动生成 + 人工可覆盖

如果设置 DEEPSEEK_API_KEY 环境变量，使用 DeepSeek 生成；
否则使用模板引擎生成（仍比纯 README 生动）。
"""
import json, os, re, subprocess, sys, urllib.request
from pathlib import Path

BASE = Path("E:/ToolPilot")
SITE_DIR = BASE / "site"
CONFIG_DIR = BASE / "config"

# ── 曦和风格模板库 ──
# 按场景/类别分配推荐语风格

SCENE_INSIGHTS = {
    "写代码": {
        "prefix": "💻 开发者的秘密武器",
        "angle": "帮你把重复劳动自动化"
    },
    "画图设计": {
        "prefix": "🎨 创意加速器",
        "angle": "让想法以视觉方式快速呈现"
    },
    "做视频": {
        "prefix": "🎬 视频创作新范式",
        "angle": "告别繁琐剪辑，专注内容本身"
    },
    "写文章": {
        "prefix": "✍️ 内容创作伙伴",
        "angle": "从零到一，帮你把想法变成文字"
    },
    "数据分析": {
        "prefix": "📊 数据洞察利器",
        "angle": "让数据说话，而不是让你加班"
    },
    "AI聊天": {
        "prefix": "💬 对话式 AI 先锋",
        "angle": "不只是聊天，是真正的智能助手"
    },
    "自动化": {
        "prefix": "⚡ 效率革命",
        "angle": "把重复的事交给机器，你做更有价值的事"
    },
}

CAT_INSIGHTS = {
    "agent": "自主 Agent 框架，让 AI 从聊天进化到干活",
    "llm": "大语言模型前沿实践",
    "rag": "知识检索增强，让 AI 不再胡说",
    "dev-tool": "开发者效率工具，好代码从好工具开始",
    "media": "AI 媒体生成，人人都能成为创作者",
    "data-science": "数据科学工具箱",
}

SOURCE_PREFIX = {
    "github": "开源社区精选",
    "hn": "HackerNews 热议",
    "producthunt": "Product Hunt 今日推荐",
    "arxiv": "最新学术前沿",
}


def generate_insight(item, force=False):
    """为核心工具生成曦和风格的推荐语"""
    title = item.get("title", "")
    source = item.get("source", "") or ""
    abstract = item.get("abstract", "") or ""
    scenes = item.get("scene", []) or []
    cats = item.get("category", []) or []
    score = int(item.get("score", 0) or 0)

    # ── 尝试 DeepSeek API ──
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if api_key:
        try:
            return _deepseek_insight(title, source, abstract, scenes, cats)
        except Exception as e:
            print(f"  ⚠ DeepSeek 调用失败: {e}，降级到模板生成")

    # ── 模板生成 ──
    return _template_insight(title, source, abstract, scenes, cats, score)


def _deepseek_insight(title, source, abstract, scenes, cats):
    """调用 DeepSeek API 生成"""
    prompt = f"""你是 AIbounty 的策展人曦和。你推荐工具时语气温暖、有观点、引人入胜。
请用一句话描述这个工具，说明它解决什么问题、有什么亮点、适合谁用。
语气像朋友推荐，不用翻译腔，不要用"您可以"这类官方用语。

工具：{title}
来源：{source}
功能描述：{abstract[:200]}
分类：{', '.join(cats)}
使用场景：{', '.join(scenes)}"""

    data = json.dumps({
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 150,
        "temperature": 0.8,
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.deepseek.com/v1/chat/completions",
        data=data,
        headers={
            "Authorization": f"Bearer {os.environ['DEEPSEEK_API_KEY']}",
            "Content-Type": "application/json"
        }
    )
    resp = json.loads(urllib.request.urlopen(req, timeout=15).read())
    return resp["choices"][0]["message"]["content"].strip()


def _template_insight(title, source, abstract, scenes, cats, score):
    """曦和风格推荐语 — 有温度、有观点、像朋友推荐"""
    # ── 打开方式 ──
    openers = [
        "曦和觉得这个工具很特别",
        "推荐给你一个好东西",
        "这个工具值得关注",
        "曦和发现了一个宝藏",
        "这个厉害了",
        "你一定会喜欢这个",
    ]
    import random
    opener = random.choice(openers)

    # ── 场景化解读 ──
    scene_readings = {
        "写代码": ["帮你把重复的编码工作自动化", "开发效率直接翻倍", "码农的福音"],
        "画图设计": ["创意到作品，只需一句话", "你的私人设计助理", "让想象力不再受工具限制"],
        "做视频": ["视频创作从未如此简单", "一个人就是一支视频团队"],
        "写文章": ["从零到一，帮你把想法变成文字", "内容创作者的加速器"],
        "数据分析": ["让数据说话，而不是让你加班", "数据洞察，一眼看穿"],
        "AI聊天": ["不只是聊天，是真正的智能助手", "对话式 AI 的标杆体验"],
        "自动化": ["把重复的事交给机器，你做更有价值的事", "效率革命的起点"],
    }

    cat_readings = {
        "agent": "自主智能体，让 AI 从「聊天」进化到「干活」",
        "llm": "大语言模型的最前沿实践",
        "rag": "让 AI 拥有长期记忆，不再「胡说八道」",
        "dev-tool": "好工具让好代码事半功倍",
        "media": "AI 生成媒体，人人都能成为创作者",
        "data-science": "数据科学家的瑞士军刀",
    }

    # ── 组合推荐语 ──
    insights = []

    # 1) 场景解读
    scene_taken = []
    for s in scenes:
        if s in scene_readings and s not in scene_taken:
            insights.append(random.choice(scene_readings[s]))
            scene_taken.append(s)
            break

    # 2) 分类解读（如果还没凑够）
    if len(insights) < 2:
        for c in cats:
            if c in cat_readings:
                insights.append(cat_readings[c])
                break

    # 3) 从摘要提取亮点
    if len(insights) < 2 and abstract:
        sentences = re.split(r'[.。!！?？\n]', abstract)
        for s in sentences:
            s = s.strip()
            if len(s) > 15 and s != title and 'badge' not in s.lower() and 'http' not in s:
                # 提取一个亮点短语
                highlight = s[:60].rstrip(',.')
                # 技术术语中文化
                highlight = _localize(highlight)
                insights.append(f"亮点：{highlight}")
                break

    # 4) 热度背书
    if source == "github" and score > 10000:
        insights.append(f"GitHub ⭐{_fmt(score)}，社区验证过的靠谱项目")
    elif source == "hn" and score > 30:
        insights.append(f"HackerNews {score} 票热议，社区认可度很高")

    # ── 最终合成 ──
    if not insights:
        insights.append(f"来自 {SOURCE_PREFIX.get(source, 'AIbounty')} 的优质工具")

    body = "，".join(insights[:3])
    return f"{opener}！{body}"


def _fmt(n):
    n = int(n or 0)
    if n > 1000000: return f"{n/1000000:.1f}M"
    if n > 1000: return f"{n/1000:.1f}k"
    return str(n)


# ── 技术术语中文化 ──
_TERM_MAP = {
    "agent": "智能体", "framework": "框架", "pipeline": "流水线",
    "workflow": "工作流", "deploy": "部署", "deployment": "部署方案",
    "embedding": "向量嵌入", "vector": "向量", "retrieval": "检索",
    "generation": "生成", "fine-tune": "微调", "training": "训练",
    "inference": "推理", "optimization": "优化", "benchmark": "基准测试",
    "toolkit": "工具包", "toolset": "工具集", "ecosystem": "生态",
    "integration": "集成", "orchestration": "编排", "automation": "自动化",
    "pipeline": "流水线", "serverless": "无服务器", "scalable": "可扩展",
    "real-time": "实时", "open source": "开源", "API": "API接口",
    "model": "模型", "dataset": "数据集", "RAG": "检索增强生成",
    "LLM": "大语言模型", "MCP": "模型上下文协议",
}

def _localize(text):
    """将英文技术术语替换为中文"""
    result = text
    # 按长度排序，优先替换长词
    for eng, cn in sorted(_TERM_MAP.items(), key=lambda x: -len(x[0])):
        result = re.sub(re.escape(eng), cn, result, flags=re.IGNORECASE)
    return result


def run():
    data_path = SITE_DIR / "data.json"
    if not data_path.exists():
        print("❌ data.json 不存在")
        return

    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    picks_config_path = CONFIG_DIR / "featured-picks.json"
    manual_ids = set()
    if picks_config_path.exists():
        picks_config = json.loads(picks_config_path.read_text("utf-8"))
        manual_ids = set(picks_config.get("manual_picks", []))

    count = 0
    for item in data.get("items", []):
        # 人工精选的不覆盖
        if item.get("id") in manual_ids:
            continue
        old_reason = item.get("reason", "")
        new_reason = generate_insight(item)
        if new_reason and new_reason != old_reason:
            item["reason"] = new_reason
            count += 1

    # 也更新 today_recommends
    for rec in data.get("today_recommends", []):
        if rec.get("id") in manual_ids:
            continue
        old = rec.get("reason", "")
        new = generate_insight(rec)
        if new and new != old:
            rec["reason"] = new
            count += 1

    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)

    print(f"✨ 曦和洞察: {count} 个工具已生成推荐语")
    if not os.environ.get("DEEPSEEK_API_KEY"):
        print(f"   （使用模板模式。设置 DEEPSEEK_API_KEY 可启用 AI 生成）")

    # 输出几个示例
    print("\n📝 推荐语示例：")
    for item in data.get("today_recommends", [])[:3]:
        print(f"  • {item.get('title','')[:40]}...")
        print(f"    → {item.get('reason','')[:80]}...")


if __name__ == "__main__":
    run()
