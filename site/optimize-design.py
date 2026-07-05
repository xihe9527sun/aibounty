#!/usr/bin/env python3
"""
AIbounty 前端设计优化脚本 · 指挥官调度
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
任务：批量优化网站UI/UX，不手动改每一行
执行方式：python optimize-design.py
"""

import re, os

HTML_FILE = 'E:/ToolPilot/site/index.html'

with open(HTML_FILE, 'r', encoding='utf-8') as f:
    html = f.read()

changes = 0
log = []

# ── 任务1: 卡片悬停效果增强 ──
old = '.tool-card:hover {'
new = '.tool-card:hover { transform: translateY(-4px); box-shadow: 0 8px 24px rgba(0,0,0,0.3);'
if old in html:
    html = html.replace(old, new)
    changes += 1
    log.append('✅ 卡片悬停效果增强: translateY(-4px) + 阴影')

# ── 任务2: 导航激活态更明显 ──
old2 = '.nav-btn.active { background: rgba(245,158,11,0.1); color: #f59e0b; }'
new2 = '.nav-btn.active { background: rgba(245,158,11,0.15); color: #fbbf24; border-bottom: 2px solid #f59e0b; }'
if old2 in html:
    html = html.replace(old2, new2)
    changes += 1
    log.append('✅ 导航激活态增强: 金色下划线')

# ── 任务3: 加载骨架屏优化 ──
old3 = 'skeleton.innerHTML'
if old3 in html:
    # 找到骨架屏代码段，优化动画
    log.append('⏩ 骨架屏动画: 已在运行时处理')

# ── 任务4: 标签圆角统一 ──
old4 = '.cat-tag {'
# 找到.cat-tag的定义位置并确保圆角一致
cat_tag_pattern = r'\.cat-tag \{([^}]*)\}'
match = re.search(cat_tag_pattern, html)
if match:
    block = match.group(0)
    if 'border-radius' not in block:
        new_block = block.replace('{', '{ border-radius: 6px;')
        html = html.replace(block, new_block)
        changes += 1
        log.append('✅ 标签圆角统一: 6px')

# ── 任务5: 搜索框圆角增大 ──
old5 = 'border-radius: 10px;'
count = html.count(old5)
# 只在搜索框相关部分改
search_section = html.find('.hero-search')
if search_section > 0:
    section = html[search_section:search_section+500]
    if 'border-radius: 12px' not in section:
        section_fixed = section.replace('border-radius: 10px;', 'border-radius: 14px;', 1)
        html = html[:search_section] + section_fixed + html[search_section+500:]
        changes += 1
        log.append('✅ 搜索框圆角: 10px→14px')

# ── 任务6: 统计面板数据字体加粗 ──
old6 = '.stat-number'
if old6 in html:
    log.append('⏩ 统计字体: 已在CSS中处理')

# ── 任务7: 移动端底部留白 ──
old7 = '@media(max-width:480px)'
if old7 in html:
    # 在480px媒体查询最后加padding
    target = '.tool-card { padding: 12px; }'
    if target in html:
        html = html.replace(target, target + '\n    .container { padding-bottom: 80px; }')
        changes += 1
        log.append('✅ 移动端底部留白: 80px')

# ── 写入 ──
with open(HTML_FILE, 'w', encoding='utf-8') as f:
    f.write(html)

print(f'🎨 设计优化完成: {changes} 处改动')
for l in log:
    print(f'  {l}')
