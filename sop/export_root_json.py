#!/usr/bin/env python3
"""导出 prey 目录到 data.json（根目录，简单格式）"""
import json, os
from pathlib import Path

PREY_DIR = Path("E:/ToolPilot/prey")
DATA_JSON = Path("E:/ToolPilot/data.json")

thresholds = {"github": 100, "hn": 5, "producthunt": 3}

def main():
    prey_files = sorted(PREY_DIR.glob("tp-*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    all_items = []
    seen = set()
    for pf in prey_files:
        try:
            with open(pf, "r", encoding="utf-8") as f:
                item = json.load(f)
        except:
            continue
        source = item.get("source", "unknown")
        # nav_hunter uses name/description; other sources use title/abstract
        title = item.get("title") or item.get("name") or ""
        abstract = item.get("abstract") or item.get("description") or ""
        key = (title, source)
        if key in seen:
            continue
        seen.add(key)

        url = item.get("url", "") or ""
        score = int(item.get("score", 0) or 0)

        if not url.startswith("http"):
            continue

        # nav_hunter: store with name/description fields (original format)
        if source == "nav_hunter":
            all_items.append({
                "source": source,
                "name": title,
                "description": abstract,
                "url": url,
                "captured_at": item.get("captured_at", ""),
            })
            continue

        # Normal quality gate for other sources
        if len(abstract.strip()) < 5:
            continue
        min_score = thresholds.get(source, 1)
        if score < min_score:
            continue

        all_items.append({
            "source": source,
            "title": title,
            "abstract": abstract,
            "url": url,
            "score": score,
            "captured_at": item.get("captured_at", ""),
        })

    data = {
        "exported_at": __import__("time").strftime("%Y-%m-%d %H:%M:%S"),
        "total": len(all_items),
        "prey": all_items,
    }
    DATA_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ data.json 已更新: {DATA_JSON} ({len(all_items)} 条)")

if __name__ == "__main__":
    main()
