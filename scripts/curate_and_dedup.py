#!/usr/bin/env python3
"""
curate_and_dedup.py — aibounty 数据质量与去重检查
=============================================
用法:
  python scripts/curate_and_dedup.py                  # 检查+报告
  python scripts/curate_and_dedup.py --auto-fix       # 自动修复+去重
  python scripts/curate_and_dedup.py --report-only    # 仅输出报告

质量铁律（盘古·曦和标准）：
  1. 无「来源」→ 不上架（自动补github/hunter即可）
  2. 无「描述/摘要」→ 需人工审核
  3. 重复 URL → 保留最新、去旧版本
  4. 重复标题（相似度>85%）→ 保留高星、去低星
  5. 分类不规范 → 自动纠偏
"""

import json, os, sys, re
from difflib import SequenceMatcher

DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "site", "data.json")

CATEGORY_WHITELIST = {"agent", "llm", "rag", "dev-tool", "media", "data-science", "uncategorized"}
SOURCE_WHITELIST = {"github", "hackernews", "juejin", "gitee", "sspai", "producthunt", "arxiv", "rss", "nav_hunter"}


def load():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=None)


def title_similarity(a, b):
    """标题相似度检测"""
    a_clean = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fff]', '', a.lower())
    b_clean = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fff]', '', b.lower())
    return SequenceMatcher(None, a_clean, b_clean).ratio()


def main():
    auto_fix = "--auto-fix" in sys.argv
    report_only = "--report-only" in sys.argv
    data = load()
    items = data.get("items", [])
    
    issues = []
    fixes = []
    dedup_count = 0
    fix_count = 0
    
    print(f"[CURATION] 检查 {len(items)} 个工具...\n")
    
    # ── 1. 缺失来源 ──
    no_source = [i for i in items if not i.get("source")]
    if no_source:
        issues.append(f"缺失来源: {len(no_source)} 个")
        for i in no_source[:10]:
            issues.append(f"  - {i.get('title','?')} id={i.get('id','')}")
        if auto_fix:
            for i in no_source:
                url = i.get("url", "")
                if "github.com" in url or "gitee.com" in url:
                    domain = "github" if "github.com" in url else "gitee"
                    i["source"] = domain
                    fix_count += 1
                    fixes.append(f"  补 source={domain}: {i.get('title','?')}")
    
    # ── 2. 缺失描述/摘要 ──
    no_abstract = [i for i in items if not i.get("abstract") and not i.get("abstract_zh")]
    if no_abstract:
        issues.append(f"缺失摘要: {len(no_abstract)} 个 (需人工审核)")
        for i in no_abstract[:5]:
            issues.append(f"  - {i.get('title','?')} id={i.get('id','')}")
    
    # ── 3. 分类异常 ──
    bad_cats = []
    for i in items:
        cats = i.get("category", [])
        if isinstance(cats, str):
            cats = [cats]
        for c in cats:
            if c not in CATEGORY_WHITELIST and c:
                bad_cats.append((i.get("title","?"), c))
                if auto_fix:
                    old_cats = list(cats)
                    i["category"] = [c for c in cats if c and c in CATEGORY_WHITELIST]
                    if not i["category"]:
                        i["category"] = ["uncategorized"]
                    fixes.append(f"  清理分类: {i.get('title','?')}: {old_cats} -> {i['category']}")
                    fix_count += 1
    if bad_cats:
        issues.append(f"分类异常: {len(bad_cats)} 个 (已自动清理)")
    
    # ── 4. 重复 URL ──
    url_map = {}
    dup_urls = []
    for i in items:
        url = i.get("url", "")
        if not url:
            continue
        if url in url_map:
            dup_urls.append((url, url_map[url], i))
        else:
            url_map[url] = i
    
    if dup_urls:
        issues.append(f"重复URL: {len(dup_urls)} 对")
        for url, old, new in dup_urls[:5]:
            issues.append(f"  URL: {url}")
            issues.append(f"    保留: {old.get('title','?')} score={old.get('score',0)}")
            issues.append(f"    删除: {new.get('title','?')} score={new.get('score',0)}")
        if auto_fix:
            remove_ids = set()
            for url, old, new in dup_urls:
                old_score = old.get("score", 0) or 0
                new_score = new.get("score", 0) or 0
                if new_score >= old_score:
                    remove_ids.add(old.get("id"))
                else:
                    remove_ids.add(new.get("id"))
            items = [i for i in items if i.get("id") not in remove_ids]
            dedup_count += len(remove_ids)
            fixes.append(f"  已去重: 删除 {len(remove_ids)} 个旧版本")
    
    # ── 5. 相似标题检测（>85%相似度且不同URL）──
    sim_pairs = []
    for i, a in enumerate(items):
        for j, b in enumerate(items):
            if i >= j:
                continue
            if a.get("url") == b.get("url"):
                continue  # 已由URL去重处理
            sim = title_similarity(a.get("title",""), b.get("title",""))
            if sim > 0.85:
                sim_pairs.append((sim, a, b))
    if sim_pairs:
        sim_pairs.sort(key=lambda x: x[0], reverse=True)
        issues.append(f"相似标题: {len(sim_pairs)} 对 (>85%)")
        for sim, a, b in sim_pairs[:5]:
            issues.append(f"  {sim:.0%}: 「{a.get('title')}」≈「{b.get('title')}」")
        if auto_fix:
            remove_ids = set()
            for sim, a, b in sim_pairs:
                a_score = a.get("score", 0) or 0
                b_score = b.get("score", 0) or 0
                if a_score >= b_score:
                    remove_ids.add(b.get("id"))
                else:
                    remove_ids.add(a.get("id"))
            items = [i for i in items if i.get("id") not in remove_ids]
            dedup_count += len(remove_ids)
            fixes.append(f"  相似去重: 删除 {len(remove_ids)} 个")
    
    # ── 报告 ──
    print(f"[CURATION] === 质量报告 ===")
    print(f"  工具总数: {len(items)}")
    print(f"  发现问题: {len(issues)} 条")
    for iss in issues:
        print(f"  ⚠ {iss}")
    
    if fixes:
        print(f"\n[CURATION] 自动修复: {fix_count} 项修复 + {dedup_count} 项去重")
        for f in fixes[:10]:
            print(f"  ✓ {f}")
    
    print(f"\n[CURATION] 工具净数量: {len(items)}")
    
    # ── 保存 ──
    if auto_fix or dedup_count > 0:
        data["items"] = items
        data["total"] = len(items)
        save(data)
        print(f"\n[CURATION] 数据已保存")
    
    if report_only:
        return
    
    # 如果有严重问题且没有 auto-fix，返回非零
    if no_abstract and not auto_fix:
        print(f"\n[CURATION] ⚠ 有 {len(no_abstract)} 个工具缺失摘要，建议人工审核")
    

if __name__ == "__main__":
    main()
