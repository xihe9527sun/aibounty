#!/usr/bin/env python3
"""修复 data.json 中 scene 字段：
1. 拼音slug → 中文标签映射
2. 字符串 → 数组统一
"""
import json

DATA = "E:/ToolPilot/site/data.json"

# Slug → 中文场景标签 映射表
SCENE_MAP = {
    # 核心场景（对应前端7个按钮）
    "biancheng":       "写代码",
    "xiezuo":          "写文章",
    "sheji":           "画图设计",
    "shuju":           "数据分析",
    "xiaolv":          "自动化",

    # 扩展映射到最接近的场景分类
    "video-generation":     "做视频",
    "text-to-speech":       "AI聊天",
    "speech-recognition":   "AI聊天",
    "voice-agent":          "AI聊天",
    "browser-automation":   "自动化",
    "gui-automation":       "自动化",
    "finance":              "数据分析",
    "quant-trading":        "数据分析",
    "data-extraction":      "数据分析",
    "vector-database":      "数据分析",
    "3d-vision":            "画图设计",
    "xitong":               "自动化",
    "security":             "自动化",
    "memory":               "自动化",
    "local-inference":       "写代码",
}

# 单字母垃圾值 → 直接丢弃
GARBAGE = {"a", "g", "i", "j", "v"}

def main():
    with open(DATA, "r", encoding="utf-8") as f:
        d = json.load(f)

    items = d.get("items", [])
    fixed_count = 0
    stats_before = {}
    stats_after = {}

    for item in items:
        old_scene = item.get("scene")
        if not old_scene:
            continue

        # 统计修复前
        if isinstance(old_scene, str):
            for s in [old_scene]:
                stats_before[s] = stats_before.get(s, 0) + 1
        elif isinstance(old_scene, list):
            for s in old_scene:
                stats_before[s] = stats_before.get(s, 0) + 1

        # 转换
        new_scenes = []
        if isinstance(old_scene, str):
            slugs = [old_scene]
        else:
            slugs = old_scene

        for slug in slugs:
            if slug in GARBAGE:
                continue
            mapped = SCENE_MAP.get(slug)
            if mapped:
                new_scenes.append(mapped)
            else:
                # 未知的保留原值但记录
                new_scenes.append(slug)

        if new_scenes:
            item["scene"] = list(set(new_scenes))  # 去重
        else:
            item["scene"] = []

        # 统计修复后
        for s in item["scene"]:
            stats_after[s] = stats_after.get(s, 0) + 1

        fixed_count += 1

    # 写回
    with open(DATA, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, separators=(",", ":"))

    print(f"Fixed {fixed_count}/{len(items)} items with scene field")
    print()
    print("Before (slug):")
    for k, v in sorted(stats_before.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v}")
    print()
    print("After (Chinese):")
    for k, v in sorted(stats_after.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v}")

    # 验证前端能匹配上的数量
    frontend_labels = ["写代码", "写文章", "画图设计", "数据分析", "AI聊天", "做视频", "自动化"]
    matched = sum(stats_after.get(l, 0) for l in frontend_labels)
    print(f"\nMatchable by frontend: {matched} total scene assignments")

if __name__ == "__main__":
    main()
