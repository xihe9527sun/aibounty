#!/usr/bin/env python3
"""
死链检测工具 — 扫描所有工具的 url 字段，标记失效链接
用法:
  python check_dead_links.py                 # 全量扫描
  python check_dead_links.py --resume        # 断点续扫（跳过已缓存的）
  python check_dead_links.py --report-only   # 只看上次结果，不扫

输出:
  reports/dead_links.json       — 详细结果（逐条）
  reports/dead_links_report.md  — 人类可读报告
"""
import sys, os, json, time, socket, ssl, urllib.request, urllib.error
from datetime import datetime, timezone
from collections import defaultdict

# ── 配置 ──
DATA_JSON = "E:/ToolPilot/site/data.json"
REPORT_DIR = "E:/ToolPilot/reports"
CACHE_FILE = os.path.join(REPORT_DIR, "dead_links_cache.json")
OUTPUT_JSON = os.path.join(REPORT_DIR, "dead_links.json")
OUTPUT_MD = os.path.join(REPORT_DIR, "dead_links_report.md")
TIMEOUT = 15  # 单请求超时（秒）
MAX_WORKERS = 20  # 并发数
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# ── HTTP 检查 ──
def check_url(url, timeout=TIMEOUT):
    """检查URL是否可访问，返回 (status, error_msg)"""
    if not url or not isinstance(url, str):
        return -1, "empty_url"
    url = url.strip()
    if not url.startswith("http"):
        return -1, "invalid_protocol"

    req = urllib.request.Request(url, method="HEAD")
    req.add_header("User-Agent", USER_AGENT)
    req.add_header("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8")
    # 不跟随重定向，我们自己判断
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        return resp.getcode(), None
    except urllib.error.HTTPError as e:
        return e.code, str(e)
    except urllib.error.URLError as e:
        # DNS 解析失败 / 连接拒绝 / 超时
        reason = str(e.reason) if hasattr(e, 'reason') else str(e)
        if "timed out" in reason.lower():
            return -2, f"timeout: {reason}"
        elif "connection refused" in reason.lower():
            return -3, f"connection_refused: {reason}"
        elif "name" in reason.lower() and "resolve" in reason.lower():
            return -4, f"dns_failed: {reason}"
        return -5, f"url_error: {reason}"
    except socket.timeout:
        return -2, "socket_timeout"
    except ssl.SSLError as e:
        # SSL 证书问题 — 也尝试 http 降级？
        return -6, f"ssl_error: {e}"
    except Exception as e:
        return -9, f"unknown: {type(e).__name__}: {e}"


def status_label(code):
    """状态码 → 人类可读标签"""
    if code is None:
        return "⏳ 未检测"
    if code == 200:
        return "✅ OK"
    if code in (301, 302, 303, 307, 308):
        return "🔀 重定向"
    if code in (401, 403):
        return "🔒 需认证"
    if code == 404:
        return "💀 404 不存在"
    if code == 410:
        return "💀 410 已删除"
    if code == 429:
        return "⏳ 429 请求过多"
    if code in (500, 502, 503):
        return "⚠️ 服务器错误"
    if code < 0:
        labels = {
            -1: "❌ 无效URL",
            -2: "⏰ 超时",
            -3: "🚫 连接拒绝",
            -4: "🌐 DNS失败",
            -5: "❌ 请求异常",
            -6: "🔐 SSL错误",
        }
        return labels.get(code, f"❌ 未知错误({code})")
    return f"⚠️ 异常状态码({code})"


def is_dead(code):
    """是否视为死链"""
    if code is None:
        return None  # 未检测
    if code in (200, 301, 302, 303, 307, 308, 401, 403, 429):
        return False  # 正常或临时问题
    if code in (404, 410, -1):
        return True   # 明确死了
    # 其他错误码（超时/DNS/连接拒绝/SSL错误/服务器错误）→ 标记为可疑
    return "suspicious"


# ── 主逻辑 ──
def load_data():
    with open(DATA_JSON, "r", encoding="utf-8") as f:
        d = json.load(f)
    return d.get("items", [])


def load_cache():
    """加载缓存（断点续扫用）"""
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_cache(cache):
    os.makedirs(REPORT_DIR, exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def scan(resume=False):
    items = load_data()
    cache = load_cache() if resume else {}
    print(f"\n  [PACK] 共 {len(items)} 个工具，缓存 {len(cache)} 条")

    results = []
    dead = []
    suspicious = []
    ok_count = 0
    skip_count = 0
    start_time = time.time()

    for idx, item in enumerate(items):
        title = item.get("title", "?")
        url = item.get("url", "")
        item_id = item.get("id", idx)

        # 缓存命中则跳过
        cache_key = str(item_id)
        if cache_key in cache and resume:
            code = cache[cache_key]["code"]
            err = cache[cache_key].get("error")
        else:
            code, err = check_url(url)
            cache[cache_key] = {"code": code, "error": err, "url": url, "title": title}
            # 每 50 个保存一次缓存
            if (idx + 1) % 50 == 0:
                save_cache(cache)

        label = status_label(code)
        dead_flag = is_dead(code)

        if dead_flag is True:
            dead.append({"id": item_id, "title": title, "url": url, "code": code, "error": err})
        elif dead_flag == "suspicious":
            suspicious.append({"id": item_id, "title": title, "url": url, "code": code, "error": err})
        else:
            ok_count += 1

        # 进度
        if (idx + 1) % 100 == 0 or idx == len(items) - 1:
            elapsed = time.time() - start_time
            pct = (idx + 1) / len(items) * 100
            print(f"  [{idx+1}/{len(items)}] {pct:.0f}% | OK={ok_count} DEAD={len(dead)} SUSP={len(suspicious)} | {elapsed:.0f}s")

    # 保存最终缓存
    save_cache(cache)

    # 输出结果
    result = {
        "scan_time": datetime.now(timezone.utc).isoformat(),
        "total": len(items),
        "ok": ok_count,
        "dead_count": len(dead),
        "suspicious_count": len(suspicious),
        "dead_links": dead,
        "suspicious_links": suspicious,
    }
    os.makedirs(REPORT_DIR, exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n  [OK] 结果已保存: {OUTPUT_JSON}")

    # 生成 Markdown 报告
    gen_report(result)
    return result


def gen_report(result):
    lines = []
    lines.append("# 💀 死链检测报告\n")
    lines.append(f"**扫描时间：** {result['scan_time']}\n")
    lines.append("| 状态 | 数量 |")
    lines.append("|------|------|")
    lines.append(f"| ✅ 正常 | {result['ok']} |")
    lines.append(f"| 💀 确认死亡 | {result['dead_count']} |")
    lines.append(f"| ⚠️ 可疑 | {result['suspicious_count']} |")
    lines.append(f"| 📦 总计 | {result['total']} |")
    lines.append("")

    if result["dead_links"]:
        lines.append("## 💀 确认死亡（建议处理）\n")
        lines.append("| 序号 | 工具名称 | 链接 | 状态 | 错误信息 |")
        lines.append("|------|----------|------|------|----------|")
        for i, d in enumerate(result["dead_links"], 1):
            err_short = (d.get("error") or "")[:60]
            lines.append(f"| {i} | {d['title']} | {d['url']} | {d['code']} | {err_short} |")
        lines.append("")

    if result["suspicious_links"]:
        lines.append("## ⚠️ 可疑（需要人工确认）\n")
        lines.append("| 序号 | 工具名称 | 链接 | 状态 | 错误信息 |")
        lines.append("|------|----------|------|------|----------|")
        for i, d in enumerate(result["suspicious_links"], 1):
            err_short = (d.get("error") or "")[:60]
            lines.append(f"| {i} | {d['title']} | {d['url']} | {d['code']} | {err_short} |")
        lines.append("")

    lines.append("---\n")
    lines.append(f"_由曦和自动检测 · 共检查 {result['total']} 条链接_")

    report = "\n".join(lines)
    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"  [OK] 报告已生成: {OUTPUT_MD}")


def report_only():
    """只看上次结果"""
    if os.path.exists(OUTPUT_JSON):
        with open(OUTPUT_JSON, "r", encoding="utf-8") as f:
            r = json.load(f)
        print(f"\n  [DATA] 上次扫描: {r['scan_time']}")
        print(f"  [OK] 正常: {r['ok']}  [DEAD] 死亡: {r['dead_count']}  [SUSP] 可疑: {r['suspicious_count']}")
        print(f"  [FILE] 报告: {OUTPUT_MD}")
        gen_report(r)
    else:
        print("  [ERR] 无上次扫描结果，请先运行 check_dead_links.py")


if __name__ == "__main__":
    os.makedirs(REPORT_DIR, exist_ok=True)
    if "--report-only" in sys.argv:
        report_only()
    else:
        resume = "--resume" in sys.argv
        scan(resume=resume)
