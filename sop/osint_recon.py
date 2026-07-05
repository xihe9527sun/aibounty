#!/usr/bin/env python3
"""
曦和 OSINT 侦察模块 v0.1
—— Phase 1 · 被动侦察（零API Key，纯公开信息）
—— 不发送任何探测包，只查询公开数据库

功能：
  1. 从狩猎数据提取工具域名
  2. crt.sh 查询子域名（Certificate Transparency）
  3. DNS 记录分析
  4. Web 技术栈识别（从响应头）
  5. 输出结构化侦察报告

用法：
  python osint_recon.py                     # 处理今日所有新猎物
  python osint_recon.py --tool "llama_index" # 指定工具名
  python osint_recon.py --all                # 重新处理全量数据
"""

import json, socket, dns.resolver, ssl, time, re, sys, os
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urlparse
import urllib.request
import html

# ── 路径配置 ──
PREY_DIR = Path("E:/ToolPilot/prey")
SITE_DIR = Path("E:/ToolPilot/site")
CONTENT_DIR = Path("E:/ToolPilot/content")
RECON_DIR = Path("E:/ToolPilot/recon")  # 新增：侦察报告目录

# ── 工具→域名 已知映射（从狩猎数据自动积累） ──
# 格式: {工具名缩写: 域名}
KNOWN_DOMAINS = {
    "llama_index": "llamaindex.ai",
    "langflow": "langflow.org",
    "crewAI": "crewai.com",
    "AutoGPT": "agpt.co",
    "MetaGPT": "deepwisdom.ai",
    "FastMCP": "fastmcp.com",
    "pytorch": "pytorch.org",
    "tensorflow": "tensorflow.org",
    "huggingface": "huggingface.co",
    "openai": "openai.com",
    "anthropic": "anthropic.com",
    "n8n": "n8n.io",
    "dify": "dify.ai",
    "langchain": "langchain.com",
    "flowise": "flowiseai.com",
    "activepieces": "activepieces.com",
    "dbeaver": "dbeaver.com",
    "elizaOS": "elizaos.ai",
    "casdoor": "casdoor.com",
    "mcp-chrome": "mcp-chrome.com",
    "headroom": "headroom.ai",
    "playwright": "playwright.dev",
    "openviking": "openviking.ai",
    "framelink": "framelink.ai",
    "vectara": "vectara.com",
    "langsmith": "smith.langchain.com",
}

# GitHub repo → 已知域名映射（自动填充热门项目）
REPO_DOMAIN_MAP = {
    "langflow-ai/langflow": "langflow.org",
    "Significant-Gravitas/AutoGPT": "agpt.co",
    "run-llama/llama_index": "llamaindex.ai",
    "PrefectHQ/fastmcp": "fastmcp.com",
    "dbeaver/dbeaver": "dbeaver.com",
    "elizaOS/eliza": "elizaos.ai",
    "activepieces/activepieces": "activepieces.com",
    "n8n-io/n8n": "n8n.io",
    "langgenius/dify": "dify.ai",
    "langchain-ai/langchain": "langchain.com",
    "FlowiseAI/Flowise": "flowiseai.com",
    "microsoft/playwright-mcp": "playwright.dev",
    "volcengine/OpenViking": "www.openviking.ai",
    "punkpeye/awesome-mcp-servers": "mcp-servers.org",
    "github/github-mcp-server": "github.com/github-mcp-server",
    "casdoor/casdoor": "casdoor.com",
    "GLips/Figma-Context-MCP": "framelink.ai",
    "chopratejas/headroom": "headroom.ai",
}

# ── 工具函数 ──

def fetch_text(url, timeout=15):
    """获取文本内容"""
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except:
        return ""

def fetch_json(url, timeout=15):
    """获取JSON"""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "OSINT-Recon/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8", errors="replace"))
    except:
        return None

def extract_domain(url_str):
    """从URL提取域名"""
    if not url_str:
        return ""
    url_str = url_str.strip()
    if not url_str.startswith(("http://", "https://")):
        url_str = "https://" + url_str
    try:
        return urlparse(url_str).hostname or ""
    except:
        return ""

def get_domain_from_tool(tool_name, tool_url=""):
    """从工具名和URL推断域名"""
    # 1. 优先从URL提取
    if tool_url:
        domain = extract_domain(tool_url)
        if domain and not domain.endswith(("github.com", "gitee.com", "huggingface.co",
                                            "producthunt.com", "reddit.com", "v2ex.com")):
            return domain

    # 2. 检查已知 repo → 域名映射
    if tool_name in REPO_DOMAIN_MAP:
        return REPO_DOMAIN_MAP[tool_name]

    # 3. 从已知映射查找
    for key, domain in KNOWN_DOMAINS.items():
        if key.lower() in tool_name.lower():
            return domain

    return ""

def query_crtsh(domain):
    """crt.sh 证书透明度日志查询 — 免费，无需API Key"""
    if not domain:
        return []
    try:
        url = f"https://crt.sh/?q={domain}&output=json"
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json"
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))

        subdomains = set()
        for entry in data:
            name = entry.get("name_value", "")
            for sub in name.split("\n"):
                sub = sub.strip()
                if sub.endswith(f".{domain}") or sub == domain:
                    if "*" not in sub:  # 排除通配符
                        subdomains.add(sub)

        # 过滤和排序
        subdomains = {s for s in subdomains if s.count(".") <= 4}  # 最多4级子域名
        return sorted(subdomains)[:50]  # 最多50条
    except Exception as e:
        return []

def resolve_dns(domain):
    """DNS 记录查询（带更短超时）"""
    if not domain:
        return {}
    result = {"A": [], "AAAA": [], "MX": [], "NS": [], "TXT": [], "CNAME": []}
    for rtype in ["A", "AAAA", "MX", "NS", "TXT", "CNAME"]:
        try:
            answers = dns.resolver.resolve(domain, rtype, lifetime=5)  # 5s 超时
            for rdata in answers:
                text = str(rdata)
                if rtype == "MX":
                    text = str(rdata.exchange)
                if text not in result[rtype]:
                    result[rtype].append(text)
        except:
            pass
        time.sleep(0.2)  # 礼貌间隔
    return result

def fetch_github_readme(repo_full_name):
    """从GitHub README提取域名信息"""
    if not repo_full_name or "/" not in repo_full_name:
        return ""
    try:
        # GitHub 公开API获取README
        url = f"https://api.github.com/repos/{repo_full_name}/readme"
        req = urllib.request.Request(url, headers={
            "User-Agent": "OSINT-Recon/1.0",
            "Accept": "application/vnd.github.v3.raw"
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read().decode("utf-8", errors="replace")

        # 跳过图片/徽章/CDN域名
        SKIP_DOMAINS = {
            "img.shields.io", "badge.fury.io", "travis-ci.org", "circleci.com",
            "codecov.io", "app.codecov.io", "coveralls.io", "cdn.travis-ci.org",
            "github.com", "gitee.com", "huggingface.co", "gitlab.com",
            "bitbucket.org", "npmjs.com", "pypi.org", "crates.io",
            "docker.com", "hub.docker.com", "www.docker.com",
            "cdn.jsdelivr.net", "unpkg.com", "raw.githubusercontent.com",
            "github.githubassets.com", "avatars.githubusercontent.com",
            "contrib.rocks", "api.star-history.com", "api.ossinsight.io",
            "repobeats.axiom.co", "opencollective.com", "twitter.com",
            "x.com", "linkedin.com", "facebook.com", "youtube.com",
            "discord.gg", "discord.com", "slack.com", "gitter.im",
            "medium.com", "dev.to", "reddit.com", "t.me", "telegram.me",
        }

        # 提取所有URL
        all_urls = re.findall(r'https?://([^\s\"\'\)\]>]+)', content)

        # 优先找主页/官网链接
        priority_signals = ["website:", "homepage:", "web:", "site:",
                           "🔗", "🌐", "🏠", "visit ", "try it",
                           "get started:", "quick start:", "docs:"]

        candidates = []
        for url_str in all_urls:
            url_str = url_str.rstrip("/.,;:!?)")
            # 解析域名
            domain_match = re.match(r'([a-zA-Z0-9][-a-zA-Z0-9]*\.(?:[a-zA-Z0-9][-a-zA-Z0-9]*\.)*[a-zA-Z]{2,})', url_str)
            if not domain_match:
                continue
            domain = domain_match.group(1).lower()

            # 跳过已知非项目域名
            base_domain = ".".join(domain.split(".")[-2:]) if domain.count(".") >= 2 else domain
            skip = False
            for sd in SKIP_DOMAINS:
                if domain == sd or domain.endswith("." + sd) or base_domain in sd:
                    skip = True
                    break
            if skip:
                continue

            # 计算优先级分数
            score = 0
            full_url = url_str
            for signal in priority_signals:
                if signal in content[max(0, content.find(full_url)-200):content.find(full_url)+len(full_url)].lower():
                    score += 5
            if not domain.startswith("www.") and domain.count(".") <= 2:
                score += 2  # 简洁域名加分
            if "docs." in domain or "app." in domain:
                score += 1

            candidates.append((score, domain, full_url))

        if candidates:
            # 按分数排序取最高分
            candidates.sort(key=lambda x: -x[0])
            best = candidates[0][1]
            print(f"    ✓ README发现域名: {best}")
            return best

        # 如果没找到好域名，尝试用项目名猜
        repo_name = repo_full_name.split("/")[-1].lower().replace("-", "").replace("_", "")
        common_domains = [f"{repo_name}.ai", f"{repo_name}.io", f"{repo_name}.com",
                          f"{repo_name}.dev", f"{repo_name}.app"]
        # 只返回如果知道是知名的
        return ""

    except Exception as e:
        print(f"    ⚠ README提取失败: {str(e)[:50]}")
        return ""

def detect_tech(domain):
    """Web技术栈识别（从响应头 + HTML 分析）"""
    if not domain:
        return {}
    result = {"headers": {}, "title": "", "server": "", "powered_by": "", "techs": []}
    try:
        url = f"https://{domain}"
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            result["status"] = resp.status
            for k, v in resp.getheaders():
                result["headers"][k.lower()] = v
            result["server"] = result["headers"].get("server", "")
            result["powered_by"] = result["headers"].get("x-powered-by", "")
            content = resp.read().decode("utf-8", errors="replace")[:5000]

            # 提取标题
            m = re.search(r'<title[^>]*>([^<]+)</title>', content, re.I)
            if m:
                result["title"] = html.unescape(m.group(1).strip())

            # 技术识别
            techs = []
            if "next.js" in content.lower() or "__NEXT_DATA__" in content:
                techs.append("Next.js")
            if "react" in content.lower() or "reactRoot" in content:
                techs.append("React")
            if "vue" in content.lower() or "vue-app" in content:
                techs.append("Vue.js")
            if "angular" in content.lower() or "ng-app" in content:
                techs.append("Angular")
            if "tailwind" in content.lower() or "cdn.tailwind" in content:
                techs.append("Tailwind CSS")
            if "jquery" in content.lower():
                techs.append("jQuery")
            if "bootstrap" in content.lower():
                techs.append("Bootstrap")
            if "wordpress" in content.lower() or "wp-content" in content:
                techs.append("WordPress")
            if "cloudflare" in content.lower() or "cloudflare" in json.dumps(result["headers"]).lower():
                techs.append("Cloudflare")
            if "nginx" in result["server"].lower():
                techs.append("Nginx")

            result["techs"] = list(set(techs))

    except Exception as e:
        result["error"] = str(e)[:100]
    return result

# ── 主侦察流程 ──

def recon_tool(tool_name, tool_url="", domain_hint="", source=""):
    """对一个工具执行完整的被动侦察"""
    domain = domain_hint or get_domain_from_tool(tool_name, tool_url)

    # 如果是GitHub项目但没有域名，从README提取
    if not domain and source == "github" and "/" in tool_name:
        print(f"    ↪ 从GitHub README提取域名...")
        readme_domain = fetch_github_readme(tool_name)
        if readme_domain:
            domain = readme_domain
            print(f"    ✓ README发现域名: {domain}")

    if not domain:
        return {"tool": tool_name, "error": "无法确定域名", "domain": ""}

    print(f"  🔍 侦察: {tool_name} → {domain}")

    report = {
        "tool": tool_name,
        "domain": domain,
        "source_url": tool_url,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # Step 1: crt.sh 子域名枚举
    try:
        subs = query_crtsh(domain)
        report["subdomains"] = subs
        print(f"    crt.sh: {len(subs)} 个子域名")
    except Exception as e:
        report["subdomains"] = []
        print(f"    crt.sh: 错误 {str(e)[:50]}")

    time.sleep(0.5)

    # Step 2: DNS 记录
    try:
        dns = resolve_dns(domain)
        report["dns"] = {k: v for k, v in dns.items() if v}
        print(f"    DNS: A={len(dns['A'])} MX={len(dns['MX'])} NS={len(dns['NS'])}")
    except Exception as e:
        report["dns"] = {}
        print(f"    DNS: 错误 {str(e)[:50]}")

    time.sleep(0.5)

    # Step 3: Web 技术识别
    try:
        tech = detect_tech(domain)
        report["web"] = {
            "title": tech.get("title", ""),
            "status": tech.get("status", 0),
            "server": tech.get("server", ""),
            "powered_by": tech.get("powered_by", ""),
            "techs": tech.get("techs", []),
        }
        print(f"    Web: {tech.get('title','?')[:40]} | {', '.join(tech.get('techs',['未知']))}")
    except Exception as e:
        report["web"] = {}
        print(f"    Web: 错误 {str(e)[:50]}")

    # 额外：尝试查主域名
    if "www." + domain not in (report.get("subdomains") or []):
        try:
            www_tech = detect_tech("www." + domain)
            if www_tech.get("status") and www_tech["status"] < 400:
                report["www_redirect"] = True
        except:
            pass

    return report


def load_hunted_tools(limit=None):
    """从狩猎数据加载工具列表（优先GitHub项目）"""
    tools = []

    # 读取所有数据
    all_items = []
    for pf in sorted(Path("E:/ToolPilot/prey").glob("tp-*.json"),
                     key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            with open(pf, "r", encoding="utf-8") as f:
                all_items.append(json.load(f))
        except:
            pass

    # 分别收集各来源
    github_items = [i for i in all_items if i.get("source") == "github"]
    ph_items = [i for i in all_items if i.get("source") == "producthunt"]
    hn_items = [i for i in all_items if i.get("source") == "hn"]
    arxiv_items = [i for i in all_items if i.get("source") == "arxiv"]

    # GitHub 项目：全部处理（每个都是工具项目）
    for item in github_items:
        name = item.get("title", "")
        if name:
            tools.append({"name": name, "url": item.get("url", ""), "source": "github"})

    # Product Hunt：全部
    for item in ph_items:
        name = item.get("title", "")
        if name:
            tools.append({"name": name, "url": item.get("url", ""), "source": "producthunt"})

    # HN：只保留工具发布帖（Show HN / Launch HN）
    for item in hn_items:
        title = item.get("title", "")
        if title.lower().startswith(("show hn:", "launch hn:")):
            tools.append({"name": title, "url": item.get("url", ""), "source": "hn"})

    # 去重
    seen = set()
    unique_tools = []
    for t in tools:
        if t["name"] not in seen:
            seen.add(t["name"])
            unique_tools.append(t)

    return unique_tools[:limit or len(unique_tools)]


def save_report(report):
    """保存侦察报告"""
    RECON_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r'[^\w\-_]', '_', report["tool"])[:50]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = RECON_DIR / f"recon_{safe_name}_{ts}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    return path


def generate_summary_report(all_reports):
    """生成汇总HTML报告"""
    if not all_reports:
        return None

    # 按有/无域名分组
    with_domain = [r for r in all_reports if r.get("domain")]
    without_domain = [r for r in all_reports if not r.get("domain")]

    html_parts = ["""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>曦和 OSINT 侦察报告</title>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body { font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; background:#0a0a0f; color:#e2e8f0; padding:40px 20px; }
  .container { max-width:1200px; margin:0 auto; }
  .nav-back { text-align:left; margin-bottom:20px; }
  .nav-back a { color:#64748b; text-decoration:none; font-size:13px; }
  .nav-back a:hover { color:#818cf8; }
  h1 { font-size:28px; background:linear-gradient(135deg,#818cf8,#a78bfa); -webkit-background-clip:text; -webkit-text-fill-color:transparent; margin-bottom:8px; }
  .sub { color:#64748b; font-size:14px; margin-bottom:32px; }
  .stats { display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:12px; margin-bottom:32px; }
  .stat-card { background:#13131f; border:1px solid #1e293b; border-radius:12px; padding:16px; text-align:center; }
  .stat-num { font-size:24px; font-weight:700; color:#818cf8; }
  .stat-label { font-size:12px; color:#64748b; margin-top:4px; }
  .card { background:#13131f; border:1px solid #1e293b; border-radius:12px; padding:20px; margin-bottom:16px; }
  .card h2 { font-size:16px; color:#e2e8f0; margin-bottom:8px; }
  .card .domain { color:#818cf8; font-size:13px; }
  .tag { display:inline-block; background:#1e293b; color:#94a3b8; padding:2px 8px; border-radius:4px; font-size:11px; margin:2px; }
  .tech-tag { background:#1a1a3e; color:#a78bfa; }
  .subdomain-list { color:#64748b; font-size:12px; line-height:1.6; max-height:80px; overflow:hidden; position:relative; }
  .subdomain-list:hover { max-height:none; }
  .no-data { color:#475569; font-style:italic; font-size:13px; }
  .grid { display:flex; flex-direction:column; gap:16px; }
  .meta-row { display:flex; gap:12px; font-size:12px; color:#64748b; margin-top:8px; flex-wrap:wrap; }
  .meta-row span { background:#1a1a2e; padding:2px 8px; border-radius:4px; }
</style>
</head>
<body>
<div class="container">
<div class="nav-back"><a href="index.html">← 返回 AIbounty</a> · <a href="xihe-status.html">✦ 曦和状态</a></div>
<h1>🔭 曦和 · OSINT 侦察报告</h1>
<p class="sub">被动侦察 · """ + datetime.now().strftime("%Y-%m-%d %H:%M") + """ · 共 """ + str(len(all_reports)) + """ 个工具</p>

<div class="stats">
  <div class="stat-card"><div class="stat-num">""" + str(len(all_reports)) + """</div><div class="stat-label">目标工具</div></div>
  <div class="stat-card"><div class="stat-num">""" + str(len(with_domain)) + """</div><div class="stat-label">已发现域名</div></div>
  <div class="stat-card"><div class="stat-num">""" + str(sum(len(r.get("subdomains",[])) for r in with_domain)) + """</div><div class="stat-label">子域名总数</div></div>
  <div class="stat-card"><div class="stat-num">""" + str(len([r for r in with_domain if r.get("web",{}).get("techs")])) + """</div><div class="stat-label">已识别技术栈</div></div>
</div>

<div class="grid">
"""]

    for report in with_domain:
        d = report["domain"]
        web = report.get("web", {})
        subs = report.get("subdomains", [])
        dns = report.get("dns", {})

        techs_html = "".join(f'<span class="tag tech-tag">{t}</span>' for t in web.get("techs", []))
        subs_html = ", ".join(subs[:20]) if subs else '<span class="no-data">无子域名记录</span>'
        url_html = f'<a href="https://{d}" target="_blank" style="color:#818cf8;text-decoration:none;">{d}</a>'

        # DNS摘要
        dns_summary = []
        if dns.get("A"):
            dns_summary.append(f'A: {dns["A"][0]}')
        if dns.get("NS"):
            dns_summary.append(f'NS: {dns["NS"][0][:20]}')
        dns_html = " · ".join(dns_summary[:3]) if dns_summary else '<span class="no-data">无</span>'

        html_parts.append(f"""
<div class="card">
  <h2>{report['tool'][:60]}</h2>
  <div class="domain">{url_html}</div>
  <div class="meta-row">
    <span>标题: {web.get('title','?')[:40]}</span>
    <span>Server: {web.get('server','?')}</span>
    <span>{'Powered by: ' + web.get('powered_by','') if web.get('powered_by') else ''}</span>
  </div>
  <div class="meta-row">
    <span>DNS: {dns_html}</span>
    <span>状态: {web.get('status','?')}</span>
  </div>
  <div style="margin:8px 0 4px;">
    {techs_html}
  </div>
  <div class="subdomain-list">
    <strong style="color:#94a3b8;font-size:12px;">子域名 ({len(subs)}): </strong>
    {subs_html}
  </div>
</div>""")

    # 无法确定域名的
    if without_domain:
        html_parts.append(f'\n<div class="card"><h2 style="color:#ef4444;">⚠ 无法确定域名 ({len(without_domain)}个)</h2><div class="no-data">' +
                          " · ".join([r['tool'][:30] for r in without_domain[:10]]) +
                          (' ...' if len(without_domain) > 10 else '') + '</div></div>')

    html_parts.append("""</div></div></body></html>""")

    # 保存
    SITE_DIR.mkdir(parents=True, exist_ok=True)
    path = SITE_DIR / "osint-report.html"
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(html_parts))
    print(f"  📄 OSINT报告: {path}")
    return path


def main():
    import argparse
    parser = argparse.ArgumentParser(description="曦和 OSINT 侦察模块")
    parser.add_argument("--tool", help="指定工具名", default="")
    parser.add_argument("--all", action="store_true", help="处理全量数据")
    parser.add_argument("--limit", type=int, default=15, help="最大工具数")
    parser.add_argument("--domain", help="手动指定域名", default="")
    args = parser.parse_args()

    print(f"\n{'='*50}")
    print(f"🔭 曦和 OSINT 侦察 v0.1")
    print(f"{'='*50}\n")

    if args.tool:
        tools = [{"name": args.tool, "url": "", "source": "manual"}]
        if args.domain:
            domain_hint = args.domain
        else:
            domain_hint = get_domain_from_tool(args.tool, "")
    else:
        tools = load_hunted_tools(args.limit if not args.all else None)
        domain_hint = ""
        print(f"从狩猎数据加载: {len(tools)} 个工具\n")

    all_reports = []
    for i, t in enumerate(tools):
        print(f"[{i+1}/{len(tools)}] {t['name']}")
        # 跳过纯代码库
        if "github.com" in t.get("url", ""):
            parts = t["name"].split("/")
            if len(parts) >= 2:
                # 尝试从项目描述猜域名
                report = recon_tool(t["name"], t.get("url", ""), domain_hint, t.get("source", ""))
            else:
                report = recon_tool(t["name"], t.get("url", ""), domain_hint, t.get("source", ""))
        else:
            report = recon_tool(t["name"], t.get("url", ""), domain_hint, t.get("source", ""))

        all_reports.append(report)
        save_report(report)
        print()

    report_path = generate_summary_report(all_reports)
    print(f"✅ OSINT 侦察完成 · {len(all_reports)} 个工具 · 报告: {report_path}")

    # 统计
    with_domain = [r for r in all_reports if r.get("domain")]
    total_subs = sum(len(r.get("subdomains", [])) for r in with_domain)
    print(f"\n📊 统计: {len(with_domain)}/{len(all_reports)} 找到域名, {total_subs} 个子域名")


if __name__ == "__main__":
    main()
