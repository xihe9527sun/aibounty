#!/usr/bin/env python3
"""submit_sitemap.py — 向各搜索引擎提交 sitemap

在日更管线中调用：在 generate_sitemap.py 之后、deploy 之前运行。
每 7 天提交一次足够，所以管线中默认跳过（只打印通知）。
手动运行：python scripts/submit_sitemap.py --force
"""

import urllib.request
import sys

SITEMAP_URL = "https://www.aibounty.cn/sitemap.xml"

ENGINES = [
    ("百度", "https://ziyuan.baidu.com/linksubmit/index?url={}&type=sitemap"),
    ("必应", "https://www.bing.com/ping?sitemap={}"),
    ("Google", "https://www.google.com/ping?sitemap={}"),
    ("IndexNow (必应)", "https://api.indexnow.org/indexnow?url={}&key=unavailable"),
]


def submit(engine_name, url_template):
    url = url_template.format(urllib.request.quote(SITEMAP_URL, safe=''))
    try:
        req = urllib.request.Request(url, method='GET')
        with urllib.request.urlopen(req, timeout=15) as resp:
            print(f'[OK] {engine_name}: HTTP {resp.status}')
            return True
    except urllib.error.HTTPError as e:
        # Some engines (Google) return 200 with no body on success
        if e.code in (200, 202, 204):
            print(f'[OK] {engine_name}: HTTP {e.code}')
            return True
        print(f'[WARN] {engine_name}: HTTP {e.code} (may need manual submission)')
        return False
    except Exception as e:
        print(f'[WARN] {engine_name}: {e}')
        return False


def main():
    force = '--force' in sys.argv

    if not force:
        # 默认不执行，只在日报管线中通知
        print('[SKIP] 跳过 sitemap 提交（默认每7天提交一次）')
        print(f'[INFO] 如需提交，运行: python {__file__} --force')
        print(f'[INFO] 也可在各搜索引擎手动提交: {SITEMAP_URL}')
        return 0

    print(f'[INFO] 提交 sitemap: {SITEMAP_URL}')
    success = 0
    for name, url_tpl in ENGINES:
        if submit(name, url_tpl):
            success += 1

    print(f'[OK] 提交完成: {success}/{len(ENGINES)} 成功')
    return 0 if success > 0 else 1


if __name__ == '__main__':
    sys.exit(main())
