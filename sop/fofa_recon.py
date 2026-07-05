#!/usr/bin/env python3
"""
曦和 FOFA 资产测绘模块 v0.1
—— Phase 2 · 主动资产测绘（免费版）

功能：
  1. 通过搜索引擎语法发现 AI 工具的公开部署
  2. 识别暴露的服务和版本信息
  3. 统计全球部署分布
  4. 生成资产测绘报告

用法：
  python fofa_recon.py --query 'title="OpenViking"'    # 直接查询
  python fofa_recon.py --tool "eliza"                   # 从狩猎数据查
  python fofa_recon.py --tool "framelink" --full         # 完整侦察

配置：
  在 config/fofa_config.json 中设置 email 和 key
  或设置环境变量 FOFA_EMAIL 和 FOFA_KEY
"""

import json, base64, urllib.request, os, sys, re, time
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urlparse

# ── 路径 ──
BASE = Path("E:/ToolPilot")
SITE_DIR = BASE / "site"
PREY_DIR = BASE / "prey"
RECON_DIR = BASE / "recon"

# FOFA API 配置
FOFA_BASE = "https://fofa.info"
FOFA_API = f"{FOFA_BASE}/api/v1/search/all"


def load_config():
    """加载 FOFA 配置"""
    config_path = BASE / "config" / "fofa_config.json"

    # 先尝试环境变量
    email = os.environ.get("FOFA_EMAIL", "")
    key = os.environ.get("FOFA_KEY", "")

    # 再尝试配置文件
    if config_path.exists():
        try:
            with open(config_path, "r") as f:
                cfg = json.load(f)
            email = email or cfg.get("email", "")
            key = key or cfg.get("key", "")
        except:
            pass

    return email, key


def fofa_search(query, email="", key="", page=1, size=50):
    """
    FOFA API 搜索
    如果未配置凭据，返回模拟数据用于演示
    """
    if not email or not key:
        return {"error": "auth_required", "message": "需要在 FOFA 注册后提供 email 和 API Key",
                "fofa_url": f"{FOFA_BASE}/result?qbase64={base64.b64encode(query.encode()).decode()}",
                "query": query,
                "results": []}

    try:
        qbase64 = base64.b64encode(query.encode()).decode()
        url = f"{FOFA_API}?email={email}&key={key}&qbase64={qbase64}&page={page}&size={size}&fields=host,title,ip,port,protocol,country,region,city,server,lastupdatetime"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())

        if data.get("error"):
            return {"error": data.get("errmsg", "API 错误"), "results": []}

        results = []
        for row in data.get("results", []):
            if len(row) >= 10:
                results.append({
                    "host": row[0],
                    "title": row[1],
                    "ip": row[2],
                    "port": row[3],
                    "protocol": row[4],
                    "country": row[5],
                    "region": row[6],
                    "city": row[7],
                    "server": row[8],
                    "last_seen": row[9],
                })
            time.sleep(0.3)

        return {"total": data.get("size", len(results)), "results": results, "error": None}

    except Exception as e:
        return {"error": str(e), "results": []}


def build_tool_queries(tool_name, domain=""):
    """根据工具名和域名生成 FOFA 查询语句"""
    queries = []

    # 从域名查询
    if domain:
        queries.append({
            "name": f"{domain} 所有子域名和服务",
            "query": f'domain="{domain}"',
            "reason": "发现该工具的所有公开部署"
        })
        queries.append({
            "name": f"{domain} Web服务",
            "query": f'host="{domain}" && protocol="http"',
            "reason": "Web服务器类型和版本"
        })

    # 从工具名查询
    name_clean = re.sub(r'[^\w\s-]', '', tool_name.split("/")[-1])
    if name_clean and len(name_clean) > 2:
        queries.append({
            "name": f"标题包含 {name_clean}",
            "query": f'title="{name_clean}"',
            "reason": "可能找到该工具的官方网站和部署"
        })

    # 通用查询：AI 工具常用技术栈
    if "ai" in tool_name.lower() or "agent" in tool_name.lower():
        queries.append({
            "name": "同类 AI Agent 框架",
            "query": 'title="AI Agent" && protocol="http" && country="CN"',
            "reason": "国内 AI Agent 部署概览"
        })

    return queries


def search_fofa_web(query, page=1):
    """
    直接从 FOFA 网页搜索（不需要 API Key）
    返回搜索结果的数量摘要
    """
    try:
        qbase64 = base64.b64encode(query.encode()).decode()
        url = f"{FOFA_BASE}/result?qbase64={qbase64}&page={page}"
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "zh-CN,zh;q=0.9",
        })
        with urllib.request.urlopen(req, timeout=20) as resp:
            html_content = resp.read().decode("utf-8", errors="replace")

        # 从页面提取结果数量
        count_match = re.search(r'共找到[^\d]*(\d[\d,]*)\s*条', html_content)
        total = count_match.group(1).replace(",", "") if count_match else "?"

        # 提取一些结果标题和链接
        results = []
        # FOFA 结果在 data-title 属性中
        titles = re.findall(r'data-title="([^"]*)"', html_content)[:10]
        hosts = re.findall(r'data-host="([^"]*)"', html_content)[:10]

        for i in range(min(len(titles), len(hosts))):
            results.append({"title": titles[i], "host": hosts[i]})

        return {
            "total_found": total,
            "web_results": results,
            "search_url": url,
            "has_api": False,
        }

    except Exception as e:
        return {"error": str(e), "total_found": "?", "results": []}


def generate_report(tool_name, domain, fofa_data, passive_data=None):
    """生成资产测绘报告"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>资产测绘: {tool_name}</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; background:#0a0a0f; color:#e2e8f0; padding:40px 20px; }}
  .container {{ max-width:1000px; margin:0 auto; }}
  h1 {{ font-size:24px; background:linear-gradient(135deg,#818cf8,#a78bfa); -webkit-background-clip:text; -webkit-text-fill-color:transparent; margin-bottom:4px; }}
  .sub {{ color:#64748b; font-size:13px; margin-bottom:24px; }}
  .card {{ background:#13131f; border:1px solid #1e293b; border-radius:12px; padding:20px; margin-bottom:16px; }}
  .card h2 {{ font-size:15px; color:#e2e8f0; margin-bottom:12px; }}
  .card .label {{ color:#64748b; font-size:12px; }}
  .card .val {{ color:#e2e8f0; font-size:13px; margin-bottom:4px; }}
  table {{ width:100%; border-collapse:collapse; font-size:13px; }}
  th {{ text-align:left; color:#64748b; font-weight:500; padding:6px 8px; border-bottom:1px solid #1e293b; }}
  td {{ padding:6px 8px; border-bottom:1px solid #1a1a2e; }}
  .tag {{ display:inline-block; background:#1e293b; color:#94a3b8; padding:2px 8px; border-radius:4px; font-size:11px; margin:2px; }}
  .warn {{ color:#f59e0b; }}
  .info {{ color:#818cf8; }}
  .action-btn {{ display:inline-block; background:#818cf8; color:#fff; padding:8px 20px; border-radius:8px; text-decoration:none; font-size:14px; margin-top:16px; }}
  .action-btn:hover {{ background:#6366f1; }}
</style>
</head>
<body>
<div class="container">
<h1>🔭 资产测绘 · {tool_name[:40]}</h1>
<p class="sub">域名: {domain} · {timestamp}</p>

<div class="card">
  <h2>📋 可查询的资产测绘</h2>
"""

    if fofa_data.get("error") == "auth_required":
        # 未配置凭据，显示注册引导
        html += f"""
  <div style="background:#1a1a3e; border:1px solid #4c1d95; border-radius:8px; padding:16px; margin-bottom:12px;">
    <p style="color:#a78bfa; font-size:14px; font-weight:500;">🔑 需要注册 FOFA 免费账号</p>
    <p style="color:#94a3b8; font-size:13px; margin:8px 0;">
      FOFA 是国内最大的网络资产搜索引擎。注册后可以查询：</p>
    <ul style="color:#94a3b8; font-size:13px; padding-left:20px; line-height:1.8;">
      <li>{domain} 的所有子域名和公开服务</li>
      <li>国内哪些服务器部署了同类型工具</li>
      <li>工具的全球部署分布（按国家/城市）</li>
      <li>暴露的服务端口和版本信息</li>
    </ul>
  </div>

  <h3 style="font-size:14px; color:#e2e8f0; margin:12px 0;">📌 可执行的查询示例</h3>
  <table>
    <tr><th>#</th><th>查询语句</th><th>用途</th></tr>
"""

        for i, q in enumerate(fofa_data.get("suggested_queries", []), 1):
            url = f"{FOFA_BASE}/result?qbase64={base64.b64encode(q['query'].encode()).decode()}"
            html += f"""    <tr>
      <td>{i}</td>
      <td><a href="{url}" target="_blank" style="color:#818cf8; text-decoration:none; word-break:break-all;">{q['query'][:60]}</a></td>
      <td style="color:#64748b;">{q['reason'][:30]}</td>
    </tr>"""

        html += """  </table>
  <p style="color:#64748b; font-size:12px; margin-top:12px;">
    ⚡ 配置后每次狩猎自动执行，无需手动操作
  </p>
"""

    elif fofa_data.get("results"):
        results = fofa_data["results"]
        html += f"""  <p style="color:#94a3b8; font-size:13px; margin-bottom:12px;">共发现 {len(results)} 条资产记录</p>
  <table>
    <tr><th>IP</th><th>端口</th><th>协议</th><th>服务</th><th>位置</th></tr>
"""
        for r in results[:20]:
            loc = f"{r.get('country','')} {r.get('city','')}" if r.get("country") else "-"
            html += f"""    <tr>
      <td style="font-family:monospace;">{r.get('host','-')}</td>
      <td>{r.get('port','-')}</td>
      <td>{r.get('protocol','-')}</td>
      <td>{r.get('server','-')[:20]}</td>
      <td>{loc}</td>
    </tr>"""
        html += "  </table>"
    else:
        # 搜索 URL 引导
        for q in fofa_data.get("suggested_queries", []):
            web_url = f"{FOFA_BASE}/result?qbase64={base64.b64encode(q['query'].encode()).decode()}"
            html += f"""  <div style="margin-bottom:8px;">
    <p style="color:#94a3b8; font-size:13px;">
      <span class="info">{q['name']}</span>
      <br>
      <span style="color:#64748b; font-size:12px;">{q['reason']}</span>
    </p>
    <p><a href="{web_url}" target="_blank" style="color:#818cf8; font-size:13px;">🔗 在 FOFA 中查看 →</a></p>
  </div>
""" if q.get("name") else ""

    # 被动侦察数据区
    if passive_data:
        html += f"""
</div>
<div class="card">
  <h2>📡 被动侦察数据</h2>
  <table>
    <tr><th>项目</th><th>值</th></tr>
    <tr><td>DNS A记录</td><td>{', '.join(passive_data.get('dns',{}).get('A',['-']))}</td></tr>
    <tr><td>DNS NS记录</td><td>{', '.join(passive_data.get('dns',{}).get('NS',['-']))}</td></tr>
    <tr><td>子域名</td><td>{len(passive_data.get('subdomains',[]))} 个</td></tr>
    <tr><td>Web服务</td><td>{passive_data.get('web',{}).get('server','-')}</td></tr>
    <tr><td>技术栈</td><td>{', '.join(passive_data.get('web',{}).get('techs',['-']))}</td></tr>
    <tr><td>页面标题</td><td>{passive_data.get('web',{}).get('title','-')[:40]}</td></tr>
  </table>
</div>"""

    html += """
</div>
</body>
</html>"""

    return html


def main():
    import argparse
    parser = argparse.ArgumentParser(description="曦和 FOFA 资产测绘模块")
    parser.add_argument("--tool", help="工具名", default="")
    parser.add_argument("--domain", help="域名", default="")
    parser.add_argument("--query", help="直接查询语句", default="")
    parser.add_argument("--demo", action="store_true", help="演示模式（不需要 API Key）")
    args = parser.parse_args()

    email, key = load_config()

    # 确定工具名和域名
    if args.tool:
        tool_name = args.tool
        domain = args.domain or ""
        # 尝试从已知域名映射获取
        osint_mod = __import__("osint_recon", fromlist=["get_domain_from_tool"])
        if not domain:
            domain = osint_mod.get_domain_from_tool(tool_name, "")
    elif args.domain:
        tool_name = args.domain
        domain = args.domain
    elif args.query:
        tool_name = "自定义查询"
        domain = ""
    else:
        print("请指定 --tool, --domain 或 --query")
        return

    print(f"\n{'='*50}")
    print(f"🔭 资产测绘: {tool_name}")
    print(f"{'='*50}")

    # 如果指定了直接查询语句
    if args.query:
        queries = [{"name": "自定义查询", "query": args.query, "reason": "自定义"}]
    else:
        queries = build_tool_queries(tool_name, domain)

    # 执行查询
    all_results = {"suggested_queries": queries, "error": "auth_required" if not email or not key else None}
    results_list = []

    if email and key and not args.demo:
        print(f"\n🔑 已配置 FOFA API，执行查询...")
        for q in queries:
            print(f"  ⟳ {q['name']}")
            result = fofa_search(q["query"], email, key)
            if result.get("results"):
                results_list.extend(result["results"])
            time.sleep(1)
        all_results = {"results": results_list, "total": len(results_list), "error": None}
        print(f"  ✓ 共 {len(results_list)} 条结果")
    else:
        status = "演示模式" if args.demo else "未配置API Key"
        print(f"\n📌 {status} — 将生成可执行的查询示例")

    # 尝试获取被动数据（从已有侦察数据）
    passive_data = None
    if domain:
        try:
            import osint_recon
            print(f"\n📡 补充被动侦察数据...")
            report = osint_recon.recon_tool(tool_name, "", domain)
            if report.get("domain"):
                passive_data = {
                    "dns": report.get("dns", {}),
                    "subdomains": report.get("subdomains", []),
                    "web": report.get("web", {}),
                }
        except:
            pass

    # 生成报告
    html = generate_report(tool_name, domain or "未知", all_results, passive_data)
    SITE_DIR.mkdir(parents=True, exist_ok=True)
    report_path = SITE_DIR / f"asset_{tool_name.split('/')[-1][:20]}.html"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"\n📄 报告: file://{report_path}")

    # 同时更新统一报告
    update_main_report(all_results, passive_data)

    print(f"\n{'='*50}")
    print("  ✅ 完成")
    print(f"{'='*50}")


def update_main_report(fofa_data, passive_data):
    """更新主资产测绘报告页面"""
    html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>曦和 资产测绘报告</title>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body { font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; background:#0a0a0f; color:#e2e8f0; padding:40px 20px; }
  .container { max-width:900px; margin:0 auto; }
  .nav-back { margin-bottom:20px; }
  .nav-back a { color:#64748b; text-decoration:none; font-size:13px; }
  .nav-back a:hover { color:#818cf8; }
  h1 { font-size:28px; background:linear-gradient(135deg,#818cf8,#a78bfa); -webkit-background-clip:text; -webkit-text-fill-color:transparent; margin-bottom:8px; }
  .sub { color:#64748b; font-size:14px; margin-bottom:32px; }
  .card { background:#13131f; border:1px solid #1e293b; border-radius:12px; padding:24px; margin-bottom:16px; }
  .card h2 { font-size:16px; margin-bottom:12px; }
  .status-dot { display:inline-block; width:8px; height:8px; border-radius:50%; margin-right:8px; }
  .dot-green { background:#22c55e; }
  .dot-amber { background:#f59e0b; }
  .dot-gray { background:#475569; }
  .step { display:flex; align-items:flex-start; gap:12px; margin-bottom:16px; }
  .step-num { width:28px; height:28px; border-radius:50%; background:#1e293b; color:#818cf8; display:flex; align-items:center; justify-content:center; font-size:14px; font-weight:600; flex-shrink:0; }
  .step-content { flex:1; }
  .step-content p { color:#94a3b8; font-size:13px; line-height:1.6; }
  .code { background:#1a1a2e; color:#a78bfa; padding:2px 6px; border-radius:4px; font-family:monospace; font-size:12px; }
</style>
</head>
<body>
<div class="container">
<div class="nav-back"><a href="index.html">← 返回 ToolPilot</a> · <a href="xihe-status.html">✦ 曦和状态</a></div>
<h1>🔭 曦和 · 资产测绘</h1>
<p class="sub">Phase 2 · 主动资产测绘 · """ + datetime.now().strftime("%Y-%m-%d") + """</p>

<div class="card">
  <h2>📊 当前状态</h2>
  <div class="step">
    <div class="step-num">1</div>
    <div class="step-content">
      <p style="font-weight:500; color:#e2e8f0;">被动侦察 <span class="status-dot dot-green"></span> 已完成</p>
      <p>域名发现 · DNS分析 · 技术栈识别 · 子域名枚举</p>
    </div>
  </div>
  <div class="step">
    <div class="step-num">2</div>
    <div class="step-content">
      <p style="font-weight:500; color:#e2e8f0;">主动测绘 <span class="status-dot dot-amber"></span> 待配置</p>
      <p>需注册 <span class="code">fofa.info</span> 免费账号，配置 API Key 后自动运行</p>
    </div>
  </div>
  <div class="step">
    <div class="step-num">3</div>
    <div class="step-content">
      <p style="font-weight:500; color:#e2e8f0;">狩猎融合 <span class="status-dot dot-gray"></span> 待启动</p>
      <p>每次狩猎后自动资产测绘 · 部署报告 · 趋势分析</p>
    </div>
  </div>
</div>

<div class="card">
  <h2>🔑 配置 FOFA</h2>
  <p style="color:#94a3b8; font-size:13px; margin-bottom:12px;">
    免费注册 <a href="https://fofa.info" target="_blank" style="color:#818cf8;">fofa.info</a>，
    在「个人中心 → API 管理」获取 API Key。
  </p>
  <p style="color:#94a3b8; font-size:13px; margin-bottom:12px;">
    然后创建配置文件 <span class="code">E:\\ToolPilot\\config\\fofa_config.json</span>：
  </p>
  <pre style="background:#1a1a2e; color:#a78bfa; padding:12px; border-radius:8px; font-size:12px; line-height:1.5; overflow-x:auto;">
{
  "email": "your@email.com",
  "key": "your_fofa_api_key"
}
  </pre>
  <p style="color:#94a3b8; font-size:13px; margin-top:12px;">
    配置完成后，每次狩猎自动执行资产测绘。
  </p>
</div>

<div class="card">
  <h2>🔍 可直接在 FOFA 中搜索的 AI 工具</h2>
"""
    # 列出现有工具的 FOFA 查询
    sdir = SITE_DIR
    reports = sorted(sdir.glob("asset_*.html"))
    if reports:
        for rp in reports[-10:]:
            name = rp.stem.replace("asset_", "").replace("_", " ").title()
            html += f'  <p><a href="{rp.name}" style="color:#818cf8; font-size:13px;">🔗 {name}</a></p>\n'
    else:
        html += '  <p style="color:#64748b; font-size:13px;">暂无资产报告，运行 fofa_recon.py 生成。</p>\n'

    html += """</div>
</div>
</body>
</html>"""

    path = SITE_DIR / "asset-report.html"
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  📄 主报告: file://{path}")


if __name__ == "__main__":
    main()
