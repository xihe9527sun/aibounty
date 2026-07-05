#!/usr/bin/env python3
"""AIbounty 数据质量检查器 · v1
每次狩猎/导出后自动运行，生成质量报告。
"""
import json, os, sys
from pathlib import Path
from datetime import datetime

SITE_DIR = Path("E:/ToolPilot/site")
REPORT_DIR = Path("E:/ToolPilot/reports")
QA_LOG = REPORT_DIR / "qa-report.html"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

def run_qa():
    data_path = SITE_DIR / "data.json"
    if not data_path.exists():
        print("❌ data.json 不存在，无法检查")
        return False

    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    items = data.get("items", [])
    issues = []
    warnings = []

    # ── 1. 空描述检查 ──
    empty_desc = [i for i in items if not i.get("abstract")]
    if empty_desc:
        issues.append({
            "level": "warning",
            "title": f"空描述工具 ({len(empty_desc)}个)",
            "items": [(i.get("id",""), i.get("title","")[:60]) for i in empty_desc[:10]]
        })

    # ── 2. 短描述检查 ──
    short_desc = [i for i in items if 0 < len(i.get("abstract","") or "") < 30]
    if short_desc:
        warnings.append({
            "title": f"描述过短 (<30字, {len(short_desc)}个)",
            "items": [(i.get("id",""), i.get("title","")[:60], len(i.get("abstract","") or "")) for i in short_desc[:10]]
        })

    # ── 3. 重复 ID 检查 ──
    ids = [i.get("id","") for i in items]
    if len(ids) != len(set(ids)):
        dupes = [id for id in ids if ids.count(id) > 1]
        issues.append({
            "level": "error",
            "title": f"重复 ID ({len(set(dupes))}个)",
            "items": list(set(dupes))
        })

    # ── 4. URL 有效性检查 ──
    bad_url = [i for i in items if not (i.get("url","") or "").startswith("http")]
    if bad_url:
        issues.append({
            "level": "error",
            "title": f"无效 URL ({len(bad_url)}个)",
            "items": [(i.get("id",""), i.get("title","")[:40]) for i in bad_url[:10]]
        })

    # ── 5. 来源分布检查 ──
    by_source = {}
    for i in items:
        s = i.get("source","unknown")
        by_source[s] = by_source.get(s, 0) + 1
    if len(by_source) < 2:
        issues.append({
            "level": "warning",
            "title": "来源单一 — 只有 1 个数据源",
            "items": list(by_source.items())
        })

    # ── 6. 缺少字段检查 ──
    required = ["id", "title", "source", "captured_at"]
    for i in items:
        for field in required:
            if not i.get(field):
                issues.append({
                    "level": "error",
                    "title": f"缺少字段: {field}",
                    "items": [(i.get("id",""), i.get("title","")[:40])]
                })
                break

    # ── 7. 无 category 检查 ──
    no_cat = [i for i in items if not i.get("category")]
    if no_cat:
        warnings.append({
            "title": f"未分类工具 ({len(no_cat)}个)",
            "items": [(i.get("id",""), i.get("title","")[:40]) for i in no_cat[:10]]
        })

    # ── 生成报告 ──
    total_issues = len([i for i in issues if i["level"] == "error"])
    total_warnings = len(issues) + len(warnings)
    status = "✅ 正常" if total_issues == 0 else f"⚠️ {total_issues}个错误"

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><title>AIbounty · 数据质量报告</title>
<style>
* {{margin:0;padding:0;box-sizing:border-box;}}
body {{font-family:-apple-system,'PingFang SC',sans-serif;background:#0a0e17;color:#e2e8f0;padding:24px;max-width:900px;margin:0 auto;}}
h1 {{color:#818cf8;font-size:22px;margin-bottom:4px;}}
.date {{color:#64748b;font-size:13px;margin-bottom:20px;}}
.status {{display:inline-block;padding:4px 14px;border-radius:100px;font-size:13px;font-weight:600;margin-bottom:20px;}}
.status.ok {{background:rgba(52,211,153,0.15);color:#34d399;}}
.status.warn {{background:rgba(245,158,11,0.15);color:#fbbf24;}}
.status.err {{background:rgba(239,68,68,0.15);color:#f87171;}}
.summary {{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:24px;}}
.card {{background:#111827;border:1px solid #1e3a5f;border-radius:10px;padding:14px;text-align:center;}}
.card .num {{font-size:28px;font-weight:700;}}
.card .num.green {{color:#34d399;}}
.card .num.yellow {{color:#fbbf24;}}
.card .num.red {{color:#f87171;}}
.card .label {{font-size:12px;color:#64748b;margin-top:4px;}}
.section {{background:#111827;border:1px solid #1e3a5f;border-radius:10px;padding:16px;margin-bottom:16px;}}
.section h2 {{font-size:15px;font-weight:600;margin-bottom:8px;}}
.section.error h2 {{color:#f87171;}}
.section.warning h2 {{color:#fbbf24;}}
.section.info h2 {{color:#818cf8;}}
.section p {{font-size:13px;color:#94a3b8;margin-bottom:6px;}}
.section ul {{list-style:none;padding:0;}}
.section li {{font-size:12px;color:#94a3b8;padding:4px 0;border-bottom:1px solid rgba(255,255,255,0.04);}}
.section li:last-child {{border-bottom:none;}}
.section .item-id {{color:#64748b;font-size:11px;margin-left:4px;}}
.section .badge {{display:inline-block;padding:1px 6px;border-radius:4px;font-size:10px;margin-right:6px;}}
.badge-error {{background:rgba(239,68,68,0.15);color:#f87171;}}
.badge-warning {{background:rgba(245,158,11,0.15);color:#fbbf24;}}
</style></head>
<body>
<h1>🏴‍☠️ AIbounty · 数据质量报告</h1>
<p class="date">{datetime.now().strftime("%Y-%m-%d %H:%M")} · 共 {len(items)} 个工具</p>
<div class="status {'ok' if status.startswith('✅') else 'warn' if total_issues==0 else 'err'}">{status}</div>
<div class="summary">
  <div class="card"><div class="num green">{len(items)}</div><div class="label">工具总数</div></div>
  <div class="card"><div class="num yellow">{total_warnings}</div><div class="label">警告</div></div>
  <div class="card"><div class="num red">{total_issues}</div><div class="label">错误</div></div>
</div>
"""

    # 来源分布
    src_rows = "".join(f'<span style="display:inline-block;margin:4px 6px 4px 0;padding:3px 10px;background:rgba(99,102,241,0.1);border-radius:6px;font-size:12px;color:#a5b4fc;">{k}: {v}</span>' for k,v in sorted(by_source.items()))
    html += f'<div class="section info"><h2>📊 来源分布</h2><div style="display:flex;flex-wrap:wrap;">{src_rows}</div></div>'

    # 问题列表
    for iss in issues:
        level = iss["level"]
        cls = "error" if level == "error" else "warning"
        badge = "错误" if level == "error" else "警告"
        html += f'<div class="section {cls}"><h2><span class="badge badge-{cls}">{badge}</span> {iss["title"]}</h2><ul>'
        for row in iss["items"][:15]:
            if isinstance(row, tuple):
                if len(row) >= 3:
                    html += f'<li>{row[1]} <span class="item-id">({row[0]}, {row[2]}字)</span></li>'
                elif len(row) == 2:
                    html += f'<li>{row[1]} <span class="item-id">({row[0]})</span></li>'
                else:
                    html += f'<li>{row[0]}</li>'
            else:
                html += f'<li>{row}</li>'
        if len(iss["items"]) > 15:
            html += f'<li style="color:#64748b;">...还有 {len(iss["items"]) - 15} 个</li>'
        html += '</ul></div>'

    for w in warnings:
        html += f'<div class="section warning"><h2>⚠️ {w["title"]}</h2><ul>'
        for row in w["items"][:10]:
            if len(row) >= 3:
                html += f'<li>{row[1]} <span class="item-id">({row[0]}, {row[2]}字)</span></li>'
            elif len(row) == 2:
                html += f'<li>{row[1]} <span class="item-id">({row[0]})</span></li>'
            else:
                html += f'<li>{row[0]}</li>'
        if len(w["items"]) > 10:
            html += f'<li style="color:#64748b;">...还有 {len(w["items"]) - 10} 个</li>'
        html += '</ul></div>'

    # 未发现问题
    if not issues and not warnings:
        html += '<div class="section info"><h2>✨ 全部通过</h2><p>所有数据检查均通过，没有发现质量问题。</p></div>'

    html += "</body></html>"

    with open(QA_LOG, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\n📋 数据质量报告: {QA_LOG}")
    print(f"   工具: {len(items)} | 错误: {total_issues} | 警告: {total_warnings}")
    return total_issues == 0


if __name__ == "__main__":
    ok = run_qa()
    sys.exit(0 if ok else 1)
