#!/usr/bin/env python3
"""AIbounty 数据导出器 v3：ID + 每日精选 + 场景分类 + 最新趋势"""
import json, hashlib, base64, re, time, os, urllib.request, html as htmlmod
from pathlib import Path
from datetime import datetime

SITE_DIR = Path("E:/ToolPilot/site")
PREY_DIR = Path("E:/ToolPilot/prey")
BASE = Path("E:/ToolPilot")
SITE_DIR.mkdir(parents=True, exist_ok=True)

# 技术分类
TECH_CATS = {
    "agent": ["agent", "autogpt", "crewai", "langgraph", "multi-agent", "自主", "智能体"],
    "llm": ["llm", "gpt", "chatgpt", "claude", "gemini", "deepseek", "大模型", "transformer"],
    "rag": ["rag", "retrieval", "向量", "embedding", "knowledge base"],
    "dev-tool": ["ide", "cursor", "copilot", "codex", "编程", "developer", "sdk", "framework"],
    "media": ["image", "video", "midjourney", "stable diffusion", "sora", "生成", "audio", "voice", "tts", "speech"],
    "data-science": ["mlflow", "pytorch", "tensorflow", "dataset", "training", "fine-tune"],
}

# 场景分类（面向用户需求）
SCENE_CATS = {
    "写代码": ["code", "programming", "developer", "ide", "cursor", "copilot", "coding", "编程", "开发"],
    "写文章": ["writing", "content", "blog", "article", "copywriting", "写作", "文案", "内容"],
    "做PPT": ["presentation", "slide", "ppt", "deck", "幻灯片"],
    "数据分析": ["data", "analytics", "analysis", "mlflow", "visualization", "数据", "分析"],
    "画图设计": ["image", "design", "midjourney", "stable diffusion", "art", "设计", "绘图", "创作"],
    "做视频": ["video", "animation", "sora", "video generation", "视频"],
    "AI聊天": ["chatbot", "chatgpt", "claude", "gemini", "对话", "聊天", "助手"],
    "自动化": ["automation", "workflow", "pipeline", "agent", "自动", "流程"],
}

def make_id(item):
    raw = f"{item.get('title','')}|{item.get('source','')}|{item.get('url','')}"
    return hashlib.md5(raw.encode()).hexdigest()[:10]

def classify(item):
    title = (item.get("title", "") + " " + item.get("abstract", "")).lower()
    tech_tags = []
    for cat, kws in TECH_CATS.items():
        if any(kw in title for kw in kws):
            tech_tags.append(cat)
    scene_tags = []
    for cat, kws in SCENE_CATS.items():
        if any(kw in title for kw in kws):
            scene_tags.append(cat)
    return {
        "tech": tech_tags or ["uncategorized"],
        "scene": scene_tags[:3]
    }

def pick_daily_picks(items):
    """算法选每日精选：高星 + 新鲜 = 加权得分"""
    now = datetime.now()
    scored = []
    for item in items:
        score = 0
        # 星数分
        star = int(item.get("score", 0) or 0)
        if star > 50000: score += 50
        elif star > 10000: score += 40
        elif star > 5000: score += 30
        elif star > 1000: score += 20
        elif star > 100: score += 10
        # 新鲜度分
        captured = item.get("captured_at", "")
        if captured:
            try:
                t = datetime.strptime(captured, "%Y-%m-%d %H:%M:%S")
                hours_ago = (now - t).total_seconds() / 3600
                if hours_ago < 6: score += 30
                elif hours_ago < 24: score += 20
                elif hours_ago < 72: score += 10
            except: pass
        scored.append((score, item))
    scored.sort(key=lambda x: -x[0])
    return [item for _, item in scored[:5]]

def detect_roles(item):
    """从已有数据推导角色归属"""
    source = item.get("source", "")
    cats = item.get("category", [])
    scenes = item.get("scene", [])
    title = (item.get("title", "") + " " + (item.get("abstract", "") or "")).lower()
    url = item.get("url", "") or ""

    roles = []
    # 开发者
    if source == "github" or "dev-tool" in cats or "写代码" in scenes or \
       any(kw in title for kw in ["sdk", "api", "framework", "cli", "library", "toolkit"]):
        roles.append("developer")
    # 创作者
    if "media" in cats or "image-video" in cats or \
       any(s in scenes for s in ["画图设计", "做视频", "写文章"]) or \
       any(kw in title for kw in ["image", "video", "music", "audio", "design", "创作", "设计", "视频"]):
        roles.append("creator")
    # 企业用户
    if item.get("region") == "cn" or \
       any(kw in title for kw in ["enterprise", "business", "team", "企业", "团队", "saas", "pricing"]):
        roles.append("enterprise")
    # 研究者
    if source == "arxiv" or \
       any(c in cats for c in ["llm", "data-science"]) or \
       any(kw in title for kw in ["research", "paper", "training", "model", "dataset", "研究", "论文", "实验"]):
        roles.append("researcher")

    return list(set(roles)) or ["general"]


def detect_data_tags(item):
    """从狩猎+OSINT数据生成智能标签"""
    source = item.get("source", "")
    score = int(item.get("score", 0) or 0)
    url = item.get("url", "") or ""
    abstract = (item.get("abstract", "") or "").lower()
    title = (item.get("title", "")).lower()

    tags = []
    # 开源
    if source in ("github", "gitee") or "github.com" in url or "gitee.com" in url:
        tags.append("open_source")
    # 国产
    if item.get("region") == "cn" or "gitee" in url:
        tags.append("made_in_china")
    # 高星
    if score > 10000:
        tags.append("high_stars")
    elif score > 1000:
        tags.append("popular")
    # 新发布（24小时内捕获）
    captured = item.get("captured_at", "")
    if captured:
        try:
            t = datetime.strptime(captured, "%Y-%m-%d %H:%M:%S")
            hours_ago = (datetime.now() - t).total_seconds() / 3600
            if hours_ago < 24:
                tags.append("fresh")
        except:
            pass
    # 企业级
    if any(kw in (title + abstract) for kw in ["enterprise", "team", "business", "security", "auth", "role"]):
        tags.append("enterprise_grade")
    # 有Demo
    if any(kw in url for kw in [".app", ".dev", ".io", ".com"]) and source != "github":
        tags.append("has_demo")

    return tags


def detect_region(item):
    """判断工具是国内还是国际"""
    source = item.get("source", "")
    title = item.get("title", "")
    abstract = item.get("abstract", "") or ""
    url = item.get("url", "") or ""
    combined = (title + " " + abstract).lower()

    # 来源判断
    cn_sources = {"juejin", "oschina", "gitee", "modelscope", "v2ex"}
    if source in cn_sources:
        return "cn"

    # .cn 域名
    if ".cn" in url and not url.endswith((".com.cn", ".net.cn", ".org.cn")):
        return "cn"

    # 中文字符比例 > 30% 判定为国内工具
    cn_chars = sum(1 for c in combined if '\u4e00' <= c <= '\u9fff')
    total_chars = max(len(combined), 1)
    if cn_chars / total_chars > 0.3:
        return "cn"

    return "global"


def generate_reason(item):
    """为工具自动生成推荐理由"""
    scene = item.get("scene", [])
    cats = item.get("category", [])
    score = int(item.get("score", 0) or 0)
    source = item.get("source", "")

    reasons = []
    if "写代码" in scene: reasons.append("编程利器")
    if "画图设计" in scene: reasons.append("设计创意必备")
    if "做视频" in scene: reasons.append("视频创作神器")
    if "数据分析" in scene: reasons.append("数据科学家标配")
    if "AI聊天" in scene: reasons.append("对话式AI标杆")
    if "自动化" in scene: reasons.append("效率提升利器")
    if "agent" in cats: reasons.append("自主Agent框架")
    if "llm" in cats: reasons.append("大语言模型前沿")
    if "rag" in cats: reasons.append("知识检索增强")
    if "dev-tool" in cats: reasons.append("开发者效率工具")
    if source == "github" and score > 10000: reasons.append(f"GitHub ⭐{fmt_star(score)} 高星项目")
    if source == "arxiv": reasons.append("最新学术论文")

    return " · ".join(reasons[:3]) or "今日新晋热门工具"


def fmt_star(n):
    n = int(n or 0)
    if n > 1000000: return f"{n/1000000:.1f}M"
    if n > 1000: return f"{n/1000:.1f}k"
    return str(n)


# ── L2 中文翻译：Helsinki-NLP/opus-mt-en-zh 离线译 abstract → abstract_zh ──

try:
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
    import torch
    TRANSFORMERS_AVAILABLE = True
    _tokenizer = None
    _model = None
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    _tokenizer = None
    _model = None


def _load_translation_model():
    """懒加载翻译模型，首次自动下载 (~300MB)"""
    global _tokenizer, _model
    if _tokenizer is None or _model is None:
        import os as _os
        if not _os.environ.get("HF_ENDPOINT"):
            _os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
        model_name = "Helsinki-NLP/opus-mt-en-zh"
        print(f"  ⬇️ 首次运行，正在下载 {model_name} (~300MB)...")
        _tokenizer = AutoTokenizer.from_pretrained(model_name)
        _model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        print("  ✅ 模型加载完成")
    return _tokenizer, _model


def _translate_batch(texts):
    """批量翻译，一次加载模型后复用"""
    tokenizer, model = _load_translation_model()
    results = [""] * len(texts)

    # 过滤空/过短文本
    valid_texts = []
    valid_indices = []
    for i, t in enumerate(texts):
        if t and len(t.strip()) >= 5:
            valid_texts.append(t.strip()[:512])
            valid_indices.append(i)
        else:
            results[i] = texts[i]

    if not valid_texts:
        return results

    # 分批翻译（每批 32 条，防 OOM）
    batch_size = 32
    for batch_start in range(0, len(valid_texts), batch_size):
        batch_texts = valid_texts[batch_start:batch_start + batch_size]
        batch_indices = valid_indices[batch_start:batch_start + batch_size]
        try:
            inputs = tokenizer(batch_texts, return_tensors="pt", padding=True, truncation=True)
            outputs = model.generate(**inputs, max_length=128)
            decoded = tokenizer.batch_decode(outputs, skip_special_tokens=True)
            for i, idx in enumerate(batch_indices):
                results[idx] = decoded[i].strip()
        except Exception as e:
            print(f"    ⚠ 批次翻译失败: {e}")
            for idx in batch_indices:
                results[idx] = texts[idx]

    return results


def translate_abstracts(items):
    """用 Helsinki-NLP/opus-mt-en-zh 将英文摘要译成中文 (零成本, 最佳质量).
    缓存确保重复导出不重复翻译. 首次需下载模型 (~300MB).
    """
    if not TRANSFORMERS_AVAILABLE:
        print("  ℹ️ transformers 未安装，abstract_zh 使用英文原文（pip install transformers sentencepiece）")
        for item in items:
            item["abstract_zh"] = item.get("abstract", "")
        return

    # ── 加载缓存 ──
    cache = {}  # item_id -> (abstract_hash, abstract_zh)
    data_path = SITE_DIR / "data.json"
    if data_path.exists():
        try:
            existing = json.loads(data_path.read_text("utf-8"))
            for e in existing.get("items", []):
                if e.get("abstract_zh") and e.get("abstract"):
                    h = hashlib.md5(e["abstract"].encode()).hexdigest()
                    cache[e["id"]] = (h, e["abstract_zh"])
        except Exception:
            pass

    # ── 筛选需要翻译的条目 ──
    to_translate = []
    indices = []
    for idx, item in enumerate(items):
        abstract = item.get("abstract", "").strip()
        if not abstract or len(abstract) < 5:
            item["abstract_zh"] = abstract
            continue
        item_id = item.get("id", "")
        h = hashlib.md5(abstract.encode()).hexdigest()
        if item_id in cache and cache[item_id][0] == h:
            item["abstract_zh"] = cache[item_id][1]
            continue
        to_translate.append(abstract)
        indices.append(idx)

    if not to_translate:
        print("  ✅ 所有摘要已翻译，缓存命中")
        return

    print(f"  🔄 正在翻译 {len(to_translate)} 个工具摘要 (opus-mt-en-zh, 零成本)...")

    # ── 推理 ──
    try:
        results = _translate_batch(to_translate)
    except Exception as e:
        print(f"  ⚠ opus-mt 翻译失败: {e}")
        for idx in indices:
            items[idx]["abstract_zh"] = items[idx].get("abstract", "")
        return

    # ── 写入 ──
    for i, idx in enumerate(indices):
        items[idx]["abstract_zh"] = results[i]

    print(f"  ✅ 翻译完成: {len(to_translate)} 条")


# ── L1 描述增强：GitHub README 拉取 ────────────────

def enrich_readme(item, cache={}):
    """从 GitHub 仓库获取 README 有意义内容增强描述"""
    url = item.get("url", "") or ""
    source = item.get("source", "")
    if source != "github" or not url or "github.com" not in url:
        return item

    abstract = item.get("abstract", "") or ""
    # 已有完整描述则跳过
    if len(abstract) > 60:
        return item

    # 解析 owner/repo
    parts = url.strip("/").rstrip(".git").split("/")
    if len(parts) < 5:
        return item
    owner, repo = parts[-2], parts[-1]
    cache_key = f"{owner}/{repo}"
    if cache_key in cache:
        item["abstract"] = cache[cache_key]
        return item

    gh_token = os.environ.get("GITHUB_TOKEN", "")
    headers = {"User-Agent": "AIbounty/3.0", "Accept": "application/vnd.github.v3.raw"}
    if gh_token:
        headers["Authorization"] = f"Bearer {gh_token}"

    for readme_file in ["README.md", "readme.md", "README.txt", "Readme.md"]:
        try:
            readme_url = f"https://api.github.com/repos/{owner}/{repo}/readme"
            req = urllib.request.Request(readme_url, headers=dict(headers, Accept="application/vnd.github.v3.raw"))
            raw = urllib.request.urlopen(req, timeout=10).read().decode("utf-8", errors="replace")
            # ── 智能内容提取 v2 ──
            lines = raw.split("\n")
            meaningful = []
            for line in lines:
                stripped = line.strip()
                # ─── 预检：跳过纯标记行 ───
                # 1. 链接/图片占比过高 (>40% 是 markdown 链接或图片)
                link_count = len(re.findall(r"\[.*?\]\(.*?\)", stripped))
                img_count = len(re.findall(r"!\[.*?\]", stripped))
                if link_count + img_count > 0:
                    link_chars = sum(len(m) for m in re.findall(r"\[.*?\]\(.*?\)", stripped))
                    if stripped and link_chars / len(stripped) > 0.4:
                        continue
                # 2. 纯徽章行：形如 [![...](...)] 或 ![...](...) 占大部分
                badge_ratio = len(re.findall(r"\[!\[.*?\]\(.*?\)\]|!\[.*?\]\(.*?\)", stripped))
                if badge_ratio >= 2:
                    continue
                # 3. 图标序列行：形如  ██╗ ██╗█████  (ASCII art / 装饰)
                ascii_art = len(re.findall(r"[█▓▒░▄▀■●◆▶▷▸▹►▻◀◁◂◃◄◅]", stripped))
                if ascii_art > 3:
                    continue
                # 4. 全符号/数字行
                if re.match(r"^[\d\s.,;:!?%&()/\\\"'\-=+@#|▶▶▷▶]+$", stripped):
                    continue
                # ─── 清理 ───
                cleaned_line = re.sub(r"https?://\S+", "", stripped)
                cleaned_line = re.sub(r"<[^>]+>", "", cleaned_line)
                cleaned_line = re.sub(r"\[.*?\]\(.*?\)", "", cleaned_line)
                cleaned_line = cleaned_line.strip()
                # ─── 后检 ───
                if len(cleaned_line) < 10:
                    continue
                # 跳过多语言/导航行
                if re.match(r"^[!#]", cleaned_line):
                    text_after = re.sub(r"!\S+\s*", "", cleaned_line).strip()
                    if len(text_after) < 8 or not re.search(r"[a-zA-Z\u4e00-\u9fff]", text_after):
                        continue
                    cleaned_line = text_after
                # 跳过"开始使用/快速开始/Getting Started"等无意义导航行
                boilerplate_kw = ["getting started", "quick start", "installation", "快速开始", "安装", "usage", "用法",
                                  "run the development server", "npm run", "prerequisites", "先决条件"]
                if any(kw in cleaned_line.lower() for kw in boilerplate_kw) and len(cleaned_line) < 40:
                    continue
                meaningful.append(cleaned_line)
                if len(" ".join(meaningful)) > 300:
                    break

            if not meaningful:
                # 如果全被过滤了，回退到 GitHub API 的 description
                return item

            cleaned = " ".join(meaningful)
            print(f"  DEBUG README [{cache_key}]: before=['{raw[:80]}'] after=['{cleaned[:80]}']")
            # 清理残留符号
            cleaned = re.sub(r"[#*`\[\]()>|~_]", "", cleaned)
            cleaned = re.sub(r"<[^>]+>", "", cleaned)
            cleaned = htmlmod.unescape(cleaned)
            cleaned = re.sub(r"\s+", " ", cleaned).strip()
            enhanced = cleaned[:300]
            if len(enhanced) > 60:
                cache[cache_key] = enhanced
                item["abstract"] = enhanced
                print(f"  📖 README 增强: {cache_key} ({len(enhanced)}字)")
            break
        except urllib.error.HTTPError as e:
            if e.code == 404:
                continue  # 尝试下一个文件名
            elif e.code == 403:
                print(f"  ⏸ GitHub API 限流，跳过 README")
                break
            else:
                print(f"  ⚠ README {cache_key}: HTTP {e.code}")
                break
        except Exception as e:
            print(f"  ⚠ README {cache_key}: {e}")
            break
        time.sleep(0.5)  # 避免限流
    return item


def export():
    prey_files = sorted(PREY_DIR.glob("tp-*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    raw_items = []
    for pf in prey_files:
        try:
            with open(pf, "r", encoding="utf-8") as f:
                raw_items.append(json.load(f))
        except:
            pass

    seen = set()
    items = []
    for item in raw_items:
        key = (item.get("title", ""), item.get("source", ""))
        if key not in seen:
            seen.add(key)

            # ── 先增强描述（READ ME 拉取） ──
            item = enrich_readme(item)

            # ── 质量门：老旧数据也过筛 ──
            url = item.get("url", "") or ""
            abstract = item.get("abstract", "") or ""
            source = item.get("source", "")
            score = int(item.get("score", 0) or 0)

            # 无有效 URL → 跳过
            if not url.startswith("http"):
                print(f"  ⛔ 过滤 {item.get('title','')[:40]}… 无有效URL")
                continue

            # 增强后仍无有效描述 → 跳过
            if len(abstract.strip()) < 5:
                print(f"  ⛔ 过滤 {item.get('title','')[:40]}… 无有效描述")
                continue

            # 分数门槛
            thresholds = {"github": 100, "hn": 5, "producthunt": 3}
            min_score = thresholds.get(source, 1)
            if score < min_score:
                print(f"  ⛔ 过滤 {item.get('title','')[:40]}… 分数未达标 ({score} < {min_score})")
                continue

            item["id"] = make_id(item)
            cats = classify(item)
            item["category"] = cats["tech"]
            item["scene"] = cats["scene"]
            item["region"] = detect_region(item)
            items.append(item)

    # 第二轮：角色和标签需要依赖已计算的 region/category/scene
    for item in items:
        item["roles"] = detect_roles(item)
        item["data_tags"] = detect_data_tags(item)

    # ── abstract_zh：DeepSeek 中文翻译 ──
    translate_abstracts(items)

    by_source = {}
    for item in items:
        src = item.get("source", "other")
        by_source.setdefault(src, []).append(item)

    cat_counts = {}
    for item in items:
        for tag in item.get("category", []):
            cat_counts[tag] = cat_counts.get(tag, 0) + 1

    scene_counts = {}
    for item in items:
        for tag in item.get("scene", []):
            scene_counts[tag] = scene_counts.get(tag, 0) + 1

    # 地区分布
    region_counts = {"cn": 0, "global": 0}
    for item in items:
        r = item.get("region", "global")
        region_counts[r] = region_counts.get(r, 0) + 1

    # 每日精选（算法）
    daily_picks = pick_daily_picks(items)

    # 今日特别推荐（人工+算法混合）
    picks_config_path = BASE / "config" / "featured-picks.json"
    today_recommends = []
    try:
        if picks_config_path.exists():
            picks_config = json.loads(picks_config_path.read_text("utf-8"))
            manual_ids = picks_config.get("manual_picks", [])
            sponsored_ids = picks_config.get("sponsored", [])

            # 手动精选优先
            manual_items = [item for item in items if item.get("id") in manual_ids]
            for mitem in manual_items:
                today_recommends.append({
                    "id": mitem["id"],
                    "title": mitem.get("title", ""),
                    "abstract": mitem.get("abstract", ""),
                    "abstract_zh": mitem.get("abstract_zh", ""),
                    "url": mitem.get("url", ""),
                    "source": mitem.get("source", ""),
                    "score": mitem.get("score", 0),
                    "category": mitem.get("category", []),
                    "scene": mitem.get("scene", []),
                    "data_tags": mitem.get("data_tags", []),
                    "pick_type": "manual",
                    "reason": "盘古特别推荐",
                })

            # 赞助推荐
            for item in items:
                if item.get("id") in sponsored_ids:
                    today_recommends.append({
                        "id": item["id"],
                        "title": item.get("title", ""),
                        "abstract": item.get("abstract", ""),
                        "abstract_zh": item.get("abstract_zh", ""),
                        "url": item.get("url", ""),
                        "source": item.get("source", ""),
                        "score": item.get("score", 0),
                        "category": item.get("category", []),
                        "scene": item.get("scene", []),
                        "data_tags": item.get("data_tags", []),
                        "pick_type": "sponsored",
                        "reason": "赞助推荐",
                    })

            # 如果没手动选，从算法精选取前3个
            if not manual_ids:
                for item in daily_picks[:3]:
                    today_recommends.append({
                        "id": item["id"],
                        "title": item.get("title", ""),
                        "abstract": item.get("abstract", ""),
                        "abstract_zh": item.get("abstract_zh", ""),
                        "url": item.get("url", ""),
                        "source": item.get("source", ""),
                        "score": item.get("score", 0),
                        "category": item.get("category", []),
                        "scene": item.get("scene", []),
                        "data_tags": item.get("data_tags", []),
                        "pick_type": "auto",
                        "reason": generate_reason(item),
                    })

            today_info = picks_config.get("today", {})
        else:
            today_info = {}
            for item in daily_picks[:3]:
                today_recommends.append({
                    "id": item["id"],
                    "title": item.get("title", ""),
                    "abstract": item.get("abstract", ""),
                    "abstract_zh": item.get("abstract_zh", ""),
                    "url": item.get("url", ""),
                    "source": item.get("source", ""),
                    "score": item.get("score", 0),
                    "category": item.get("category", []),
                    "scene": item.get("scene", []),
                    "data_tags": item.get("data_tags", []),
                    "pick_type": "auto",
                    "reason": generate_reason(item),
                })
            today_info = {}
    except Exception as e:
        print(f"  ⚠ 读取精选配置失败: {e}")
        today_info = {}
        today_recommends = []


    data = {
        "total": len(items),
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "sources": {k: len(v) for k, v in by_source.items()},
        "regions": region_counts,
        "categories": cat_counts,
        "scenes": scene_counts,
        "daily_picks": daily_picks,
        "today_recommends": today_recommends,
        "today_info": today_info,
        "trending": sorted(items, key=lambda x: int(x.get("score", 0) or 0), reverse=True)[:8],
        "items": items[:200],
    }

    out_path = SITE_DIR / "data.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    print(f"📊 数据已导出: {out_path} ({data['total']} 条, 精选{len(daily_picks)}个)")

    # 曦和洞察引擎：生成推荐语
    print("\n✨ 生成曦和推荐语...")
    insight_script = BASE / "sop" / "xihe_insight.py"
    if insight_script.exists():
        import subprocess, sys
        r = subprocess.run([sys.executable, str(insight_script)], capture_output=True, text=True)
        for line in r.stdout.strip().split("\n"):
            if line.strip():
                print(f"   {line.strip()}")
        if r.returncode != 0:
            print(f"   ⚠ 洞察引擎异常: {r.stderr.strip()[:100]}")

    return data

if __name__ == "__main__":
    export()
