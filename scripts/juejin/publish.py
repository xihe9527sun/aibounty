#!/usr/bin/env python3
"""juejin_auto_publish.py - 掘金文章自动发布工具

用法:
  python scripts/juejin/publish.py <markdown_file> [--draft-only] [--cookie SESSIONID]

依赖: Python 3.7+ 标准库（零外部依赖）

API 来源：浏览器抓包分析（2026-03-10 验证可用）
"""

import json
import re
import sys
import os
import time
import urllib.request
import urllib.error

# ── 配置 ──
API_BASE = "https://api.juejin.cn"
COOKIE_FILE = os.path.join(os.path.dirname(__file__), "juejin.env")

# 默认分类和标签
DEFAULT_CATEGORY = "6809637773935378440"   # AI
DEFAULT_TAGS = ["6809640445233070098"]     # AI工具


def load_cookie(override=None):
    """加载 Cookie，优先使用命令行参数"""
    if override:
        return f"sessionid={override}"
    if os.path.exists(COOKIE_FILE):
        with open(COOKIE_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                key, _, val = line.partition("=")
                key = key.strip().removeprefix("export").strip()
                val = val.strip().strip('"').strip("'")
                if key == "JUEJIN_COOKIE":
                    return val
        print(f"[WARN] juejin.env 中未找到 JUEJIN_COOKIE")
    return None


def api_post(path, data, cookie):
    """发送 POST 请求到掘金 API"""
    url = f"{API_BASE}{path}"
    payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Cookie": cookie,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Referer": "https://juejin.cn/",
        "Origin": "https://juejin.cn",
    }
    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return body
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        print(f"[ERR] HTTP {e.code}: {err_body[:300]}")
        return None


def parse_markdown(filepath):
    """解析 Markdown 文件，提取 frontmatter 和正文"""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    meta = {}
    body = content

    # 提取 YAML frontmatter
    fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if fm_match:
        fm_text = fm_match.group(1)
        body = content[fm_match.end():]
        for line in fm_text.splitlines():
            if ":" in line:
                k, _, v = line.partition(":")
                meta[k.strip()] = v.strip().strip('"').strip("'")

    # 从正文提取标题（取第一个 # 标题）
    if "title" not in meta:
        title_match = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
        if title_match:
            meta["title"] = title_match.group(1).strip()
        else:
            meta["title"] = os.path.basename(filepath).replace(".md", "")

    # 清理正文中的图片链接等
    body = re.sub(r">\s*!\[.*?\]\(.*?\)\s*<", "> ", body)

    return meta, body.strip()


def generate_brief(meta, body, min_len=50, max_len=100):
    """生成符合掘金要求的摘要（50-100字）"""
    if "description" in meta and meta["description"]:
        brief = meta["description"]
        if min_len <= len(brief) <= max_len:
            return brief
        if len(brief) > max_len:
            return brief[:max_len]

    # 从正文提取纯文本生成摘要
    plain = re.sub(r"```.*?```", "", body, flags=re.DOTALL)
    plain = re.sub(r"[#*`>\[\]!|]", "", plain)
    plain = re.sub(r"\s+", " ", plain).strip()
    if len(plain) > max_len:
        return plain[:max_len]
    elif len(plain) < min_len:
        return plain + "。" * ((min_len - len(plain)) // 2 + 1)
    return plain


def create_draft(title, body, brief, category_id, tag_ids, cover_image="", cookie=""):
    """创建草稿"""
    path = "/content_api/v1/article_draft/create"
    data = {
        "category_id": category_id,
        "tag_ids": tag_ids,
        "title": title,
        "brief_content": brief,
        "edit_type": 10,          # Markdown 模式
        "mark_content": body,
        "cover_image": cover_image,
        "html_content": "",
        "link_url": "",
        "theme_ids": [],
    }
    result = api_post(path, data, cookie)
    if result:
        # 响应结构：data 直接包含 id 字段，或嵌套在 article_draft 下
        draft_data = result.get("data", {})
        if not draft_data:
            print(f"[ERR] 创建草稿失败: {result}")
            return None
        # 尝试多种字段名
        draft_id = (draft_data.get("id")
                    or draft_data.get("draft_id")
                    or (draft_data.get("article_draft") or {}).get("id")
                    or (draft_data.get("article_draft") or {}).get("draft_id"))
        if draft_id:
            print(f"[OK] 草稿已创建: {draft_id}")
            return str(draft_id)
    print(f"[ERR] 创建草稿失败（无法提取ID）: {json.dumps(result, ensure_ascii=False)[:300]}")
    return None


def publish_draft(draft_id, cookie=""):
    """发布草稿为文章"""
    path = "/content_api/v1/article/publish"
    data = {
        "draft_id": draft_id,
        "sync_to_org": False,
        "column_ids": [],
        "theme_ids": [],
    }
    result = api_post(path, data, cookie)
    if result:
        article_info = result.get("data", {})
        article_id = (article_info.get("article_info") or {}).get("article_id")
        if article_id:
            url = f"https://juejin.cn/post/{article_id}"
            print(f"[OK] 文章已发布: {url}")
            return article_id
        else:
            print(f"[WARN] 发布响应无 article_id: {result}")
    else:
        print(f"[ERR] 发布失败")
    return None


def main():
    import argparse
    # Windows GBK console 兼容
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    parser = argparse.ArgumentParser(description="掘金自动发布工具")
    parser.add_argument("file", help="Markdown 文章文件路径")
    parser.add_argument("--draft-only", action="store_true", help="仅创建草稿不发布")
    parser.add_argument("--cookie", help="sessionid 值（覆盖配置文件）")
    parser.add_argument("--category", default=DEFAULT_CATEGORY, help="分类 ID")
    args = parser.parse_args()

    if not os.path.isfile(args.file):
        print(f"[ERR] 文件不存在: {args.file}")
        sys.exit(1)

    # 加载 Cookie
    cookie = load_cookie(args.cookie)
    if not cookie:
        print("[ERR] 未找到 Cookie，请通过 --cookie 参数提供 sessionid，或创建 scripts/juejin/juejin.env 文件")
        sys.exit(1)

    # 解析 Markdown
    meta, body = parse_markdown(args.file)
    title = meta.get("title", "无标题")
    brief = generate_brief(meta, body)
    category_id = meta.get("category_id", args.category)
    tag_ids_str = meta.get("tag_ids", "")
    tag_ids = [t.strip() for t in tag_ids_str.split(",") if t.strip()] if tag_ids_str else DEFAULT_TAGS
    cover_image = meta.get("cover", "")

    print(f"[INFO] 标题: {title}")
    print(f"[INFO] 摘要({len(brief)}字): {brief}")
    print(f"[INFO] 分类: {category_id}, 标签: {tag_ids}")

    # 创建草稿
    draft_id = create_draft(title, body, brief, category_id, tag_ids, cover_image, cookie)
    if not draft_id:
        sys.exit(1)

    if args.draft_only:
        print("[INFO] --draft-only 模式，未发布")
        return

    # 等待一下让系统处理草稿
    time.sleep(2)

    # 发布
    publish_draft(draft_id, cookie)


if __name__ == "__main__":
    main()
