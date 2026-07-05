#!/usr/bin/env python3
"""validate_output.py — AIbounty 数据验证与自动修复

在 daily_auto.py 跑完后调用，确保 data.json 的数据完整性。
- 修复 categories 中的脏键（单字符键、乱码键）
- 修复 today_recommends 为空或字段缺失
- 修复 trending 为空或字段缺失
- 校验字段完整性，报告数据健康度
- 可选：触发 webhook 告警

用法：
    python validate_output.py                  # 验证+修复 site/data.json
    python validate_output.py --check-only     # 仅检查，不写回
    python validate_output.py --webhook URL    # 触发 webhook 告警
"""

import json, sys, os, time
from collections import Counter

DATA_PATH = r"E:\ToolPilot\site\data.json"
VALID_CATS = {'agent', 'llm', 'rag', 'dev-tool', 'data-science', 'media', 'uncategorized', 'image-video'}

def load():
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def save(data):
    with open(DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def clean_categories(data):
    """从 items 重算 categories，清理脏键"""
    items = data.get('items', [])
    cat_cnt = Counter()
    for item in items:
        cats = item.get('category') or []
        if isinstance(cats, str):
            try: cats = json.loads(cats)
            except: cats = []
        for c in cats:
            if c and len(c) > 2:  # 只保留正常长度的键
                cat_cnt[c] += 1
    old = data.get('categories', {})
    clean = dict(cat_cnt.most_common())
    dirty_keys = [k for k in old if k not in clean or len(k) <= 2]
    removed = len([k for k in dirty_keys if k in old])
    data['categories'] = clean
    return removed, len(clean)

def validate_items(items):
    """检查每个 item 的必填字段"""
    results = {'ok': 0, 'no_title': 0, 'no_abstract': 0, 'no_abstract_zh': 0,
               'no_url': 0, 'no_category': 0, 'no_score': 0,
               'short_abstract': 0, 'short_abstract_zh': 0,
               'template_risk': 0}
    triggers = [
        "Built for getting things done", "Tired of switching tools",
        "效率直接拉满", "帮你discovering", "帮你exploring",
        "每一个 **", "自从用了 **", "终于有了一个能帮你", "别找了，就是它",
    ]
    for item in items:
        ok = True
        if not item.get('title'): results['no_title'] += 1; ok = False
        if not item.get('url'): results['no_url'] += 1; ok = False
        if not item.get('category'): results['no_category'] += 1; ok = False
        if not item.get('score') or int(item.get('score', 0) or 0) <= 0: results['no_score'] += 1
        abs_en = item.get('abstract', '') or ''
        abs_zh = item.get('abstract_zh', '') or ''
        if not abs_en: results['no_abstract'] += 1
        elif len(abs_en) < 40: results['short_abstract'] += 1
        if not abs_zh: results['no_abstract_zh'] += 1
        elif len(abs_zh) < 20: results['short_abstract_zh'] += 1
        for t in triggers:
            if t in abs_en or t in abs_zh:
                results['template_risk'] += 1
                break
        if ok: results['ok'] += 1
    return results

def is_valid_item(obj):
    """检查一个对象是否是有效的工具条目（有 title 且非空）"""
    if not isinstance(obj, dict): return False
    title = obj.get('title', '')
    if not title or not str(title).strip(): return False
    return True

def fix_trending(data):
    """修复热门趋势：从 items 中按分数排序选取"""
    items = data.get('items', [])
    trend = data.get('trending', [])
    
    # 检查现有趋势是否有效
    valid = [t for t in trend if is_valid_item(t)]
    if valid:
        return 0, len(valid)
    
    # 按分数降序
    sorted_items = sorted(items, key=lambda x: -(int(x.get('score', 0)) if x.get('score') else 0))
    new_trend = []
    used_ids = set()
    for i in sorted_items:
        if i.get('id') and i['id'] not in used_ids and len(new_trend) < 8:
            t = {k: v for k, v in i.items() if k not in ('name','description','slug')}
            new_trend.append(t)
            used_ids.add(i['id'])
    
    old_count = len(trend)
    data['trending'] = new_trend
    return old_count, len(new_trend)

def fix_today_recommends(data):
    """修复今日推荐：从 items 中选出分数最高的国内/国际工具"""
    items = data.get('items', [])
    recs = data.get('today_recommends', [])
    
    # 检查现有推荐是否有效
    valid = [r for r in recs if is_valid_item(r)]
    if valid:
        return 0, len(valid)
    
    # 从 items 选：1个国内最高分 + 2个全球最高分
    cn = sorted([i for i in items if i.get('region') == 'cn'],
                key=lambda x: -(int(x.get('score', 0)) if x.get('score') else 0))
    gl = sorted([i for i in items if i.get('region') == 'global'],
                key=lambda x: -(int(x.get('score', 0)) if x.get('score') else 0))
    fav = sorted([i for i in items if i.get('isFavorite')],
                 key=lambda x: -(int(x.get('score', 0)) if x.get('score') else 0))
    
    # 先用 favorite，不够再用高分补
    new_recs = []
    used_ids = set()
    for pool in [fav, gl[:5], cn[:3]]:
        for i in pool:
            if i.get('id') and i['id'] not in used_ids and len(new_recs) < 3:
                rec = {k: v for k, v in i.items() if k not in ('name','description','slug')}
                rec['pick_type'] = 'auto'
                rec['reason'] = f"⭐ {i.get('score', 0)} — 精选推荐"
                rec['reason_cn'] = f"⭐ {i.get('score', 0)} 星，社区推荐"
                rec['reason_en'] = f"⭐ {i.get('score', 0)} stars, community pick"
                new_recs.append(rec)
                used_ids.add(i['id'])
    
    old_count = len(recs)
    data['today_recommends'] = new_recs
    return old_count, len(new_recs)

def fix_daily_picks(data):
    """修复每日精选"""
    items = data.get('items', [])
    picks = data.get('daily_picks', [])
    
    valid = [p for p in picks if is_valid_item(p)]
    if valid:
        return 0, len(valid)
    
    gl = sorted([i for i in items if i.get('region') == 'global'],
                key=lambda x: -(int(x.get('score', 0)) if x.get('score') else 0))
    cn = sorted([i for i in items if i.get('region') == 'cn'],
                key=lambda x: -(int(x.get('score', 0)) if x.get('score') else 0))
    new_picks = []
    for i in (gl[:3] + cn[:2]):
        p = {k: v for k, v in i.items() if k not in ('name','description','slug')}
        p['pick_type'] = 'auto'
        new_picks.append(p)
    
    data['daily_picks'] = new_picks[:5]
    return len(picks), len(new_picks)

def main():
    check_only = '--check-only' in sys.argv
    webhook_url = None
    for arg in sys.argv:
        if arg.startswith('--webhook='):
            webhook_url = arg.split('=', 1)[1]
    
    print(f"  >> AIbounty 数据验证 << {'[检查模式]' if check_only else '[修复模式]'}")
    print(f"  {'='*45}")
    
    data = load()
    items = data.get('items', [])
    
    # ── 1. 校验 items ──
    print(f"\n  📦 Items: {len(items)} 个工具")
    vr = validate_items(items)
    print(f"     ✅ 完整: {vr['ok']}")
    flags = []
    if vr['no_title']: flags.append(f"❌ 缺标题: {vr['no_title']}")
    if vr['no_url']: flags.append(f"❌ 缺URL: {vr['no_url']}")
    if vr['no_abstract']: flags.append(f"⚠️ 缺EN描述: {vr['no_abstract']}")
    if vr['no_abstract_zh']: flags.append(f"⚠️ 缺ZH描述({vr['no_abstract_zh']})")
    if vr['short_abstract']: flags.append(f"⚠️ EN过短<40: {vr['short_abstract']}")
    if vr['short_abstract_zh']: flags.append(f"⚠️ ZH过短<20: {vr['short_abstract_zh']}")
    if vr['template_risk']: flags.append(f"⚠️ 模板风险: {vr['template_risk']}")
    if vr['no_category']: flags.append(f"❌ 缺分类: {vr['no_category']}")
    if vr['no_score']: flags.append(f"⚠️ 分值为0: {vr['no_score']}")
    for f in flags: print(f"     {f}")
    
    # ── 2. 修复 categories ──
    rm, keep = clean_categories(data)
    if rm:
        print(f"\n  🧹 Categories: 移除 {rm} 个脏键, 保留 {keep} 个")
    else:
        print(f"\n  ✅ Categories: {keep} 个, 无脏键")
    
    # ── 3. 修复 today_recommends ──
    old_r, new_r = fix_today_recommends(data)
    if new_r != old_r or old_r == 0:
        print(f"  🏆 今日推荐: {old_r} → {new_r} 条 {'(已修复)' if new_r > old_r else '(无需修复)'}")
        for i, r in enumerate(data['today_recommends']):
            print(f"     {i+1}. {r.get('title','?')[:40]} | ⭐{r.get('score',0)}")
    
    # ── 4. 修复 trending ──
    old_t, new_t = fix_trending(data)
    if old_t == 0 or new_t != old_t:
        print(f"\n  🔥 热门趋势: {old_t} → {new_t} 条 {'(已修复)' if new_t > old_t else '(无需修复)'}")
        for i, t in enumerate(data['trending'][:5]):
            print(f"     {i+1}. {t.get('title','?')[:40]} | ⭐{t.get('score',0)}")
    
    # ── 5. 修复 daily_picks ──
    old_p, new_p = fix_daily_picks(data)
    if old_p == 0 or new_p != old_p:
        print(f"\n  📰 每日精选: {old_p} → {new_p} 条 {'(已修复)' if new_p > old_p else '(无需修复)'}")
    
    # ── 6. 更新时间戳 ──
    data['validated_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
    
    # ── 7. 写入 ──
    if check_only:
        print(f"\n  📋 检查模式，未写入文件")
    else:
        save(data)
        print(f"\n  ✅ data.json 已更新并保存")
    
    # ── 8. 摘要 ──
    en_pct = (len(items) - vr['no_abstract']) / len(items) * 100 if items else 0
    zh_pct = (len(items) - vr['no_abstract_zh']) / len(items) * 100 if items else 0
    print(f"\n  📊 数据健康度摘要")
    print(f"     工具总数: {len(items)}")
    print(f"     EN描述覆盖率: {en_pct:.1f}%")
    print(f"     ZH描述覆盖率: {zh_pct:.1f}%")
    print(f"     分类数: {len(data.get('categories', {}))}")
    print(f"     今日推荐: {len(data.get('today_recommends', []))}")
    print(f"     热门趋势: {len(data.get('trending', []))}")
    print(f"     数据版本: {data.get('updated_at', '未知')}")
    print(f"     验证时间: {data['validated_at']}")
    
    # ── 9. 告警 ──
    has_critical = vr['no_title'] > 0 or vr['no_url'] > 0
    if has_critical:
        print(f"\n  🚨 存在严重数据问题！")
    
    if webhook_url and (has_critical or vr['no_abstract_zh'] > 100):
        try:
            import urllib.request
            body = json.dumps({
                'text': f"🤖 AIbounty 数据告警\n"
                        f"• 工具总数: {len(items)}\n"
                        f"• 缺标题: {vr['no_title']}\n"
                        f"• 缺ZH描述: {vr['no_abstract_zh']}\n"
                        f"• 验证时间: {data['validated_at']}"
            }).encode()
            r = urllib.request.Request(webhook_url, data=body,
                headers={'Content-Type': 'application/json'})
            urllib.request.urlopen(r, timeout=10)
            print(f"  📡 Webhook 告警已发送")
        except:
            print(f"  ⚠️ Webhook 发送失败")
    
    return 0 if not has_critical else 1

if __name__ == '__main__':
    sys.exit(main())
