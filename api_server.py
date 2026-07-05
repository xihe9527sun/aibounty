"""
AIbounty API Server — 薄后端
=============================
用法:
    python api_server.py              # 生产模式 (port 4321)
    python api_server.py --port 8080  # 指定端口
    python api_server.py --dev        # 热重载模式

功能:
    1. 加载 site/data.json 缓存到内存
    2. 提供 REST API 接口
    3. 挂载 site/ 静态文件（替代 server.js）
    4. 健康检查和数据保鲜监控
"""

import json, os, sys, time, threading
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ── 路径 ──
BASE_DIR = Path(__file__).parent.resolve()
DATA_PATH = BASE_DIR / "site" / "data.json"
SITE_DIR = BASE_DIR / "site"

# ── 全局数据缓存 ──
DATA = {}
DATA_LOCK = threading.Lock()
LAST_LOAD = 0
STALE_HOURS = 12  # 超过12小时视为数据过期

def load_data():
    """重新加载 data.json 到内存"""
    global DATA, LAST_LOAD
    try:
        with open(DATA_PATH, 'r', encoding='utf-8') as f:
            raw = json.load(f)
        with DATA_LOCK:
            DATA = raw
            LAST_LOAD = time.time()
        return True
    except Exception as e:
        print(f"[API] 加载失败: {e}")
        return False

def get_data():
    """获取数据缓存，自动判断是否过期"""
    with DATA_LOCK:
        if not DATA:
            return {}, False
        age_hours = (time.time() - LAST_LOAD) / 3600
        return DATA, age_hours > STALE_HOURS

# ── 分页工具 ──
def paginate(items, page=1, size=20):
    total = len(items)
    total_pages = max(1, (total + size - 1) // size)
    page = max(1, min(page, total_pages))
    start = (page - 1) * size
    end = start + size
    return {
        "items": items[start:end],
        "page": page,
        "size": size,
        "total": total,
        "total_pages": total_pages,
    }

# ═══════════════════════════════════════
# FastAPI 应用
# ═══════════════════════════════════════

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动
    if not load_data():
        print("[API] ⚠️ 首次加载失败，静态文件仍可访问")
    yield
    # 关闭（无需清理）

app = FastAPI(
    title="AIbounty API",
    version="1.0.0",
    description="AI 工具聚合导航站后端API",
    docs_url="/api/docs",
    lifespan=lifespan,
)

# CORS（允许前端跨域）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ═══════════════════════════════════════
# API 接口
# ═══════════════════════════════════════

@app.get("/health")
def health():
    """健康检查"""
    data, stale = get_data()
    age_hours = round((time.time() - LAST_LOAD) / 3600, 1) if LAST_LOAD else 0
    status = "ok"
    if stale:
        status = "stale"
    if not data:
        status = "no_data"
    
    return {
        "status": status,
        "version": "1.0.0",
        "tools_count": len(data.get("items", [])),
        "data_age_hours": age_hours,
        "data_updated_at": data.get("updated_at", "unknown"),
        "cache_loaded": bool(DATA),
    }

@app.get("/api/reload")
def reload_data():
    """手动触发数据重载"""
    ok = load_data()
    return {"success": ok, "message": "数据已重载" if ok else "加载失败"}


@app.get("/api/tools")
def list_tools(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=9999),
    category: str = Query(None),
    source: str = Query(None),
    scene: str = Query(None),
    region: str = Query(None),
    tag: str = Query(None),
    search: str = Query(None),
    sort: str = Query("score", pattern="^(score|time|interleave)$"),
):
    """列出工具，支持筛选、搜索、排序、分页"""
    data, _ = get_data()
    items = list(data.get("items", []))
    
    # 筛选
    if category and category != "all":
        items = [i for i in items if category in (i.get("category") or [])]
    if source and source != "all":
        if source == "high-score":
            items = [i for i in items if i.get("source") == "github" and int(i.get("score", 0) or 0) > 10000]
        else:
            items = [i for i in items if i.get("source") == source]
    if scene and scene != "all":
        items = [i for i in items if scene in (i.get("scene") or [])]
    if region and region != "all":
        items = [i for i in items if i.get("region") == region]
    if tag and tag != "all":
        items = [i for i in items if tag in (i.get("data_tags") or [])]
    
    # 搜索
    if search:
        q = search.lower()
        items = [i for i in items if
                 q in (i.get("title") or "").lower() or
                 q in (i.get("abstract") or "").lower() or
                 q in (i.get("abstract_zh") or "").lower() or
                 q in (i.get("source") or "").lower()]
    
    # 排序
    if search:
        pass  # 搜索时保持原序（相关性）
    elif sort == "score":
        items.sort(key=lambda x: -(int(x.get("score", 0)) if x.get("score") else 0))
    elif sort == "time":
        items.sort(key=lambda x: x.get("captured_at", ""), reverse=True)
    
    return paginate(items, page, size)


class ToolUpdate(BaseModel):
    abstract: Optional[str] = None
    abstract_zh: Optional[str] = None

@app.get("/api/tools/{item_id}")
def get_tool(item_id: str):
    """获取单个工具详情"""
    data, _ = get_data()
    for item in data.get("items", []):
        if item.get("id") == item_id:
            return item
    raise HTTPException(status_code=404, detail="工具不存在")


@app.put("/api/tools/{item_id}")
def update_tool(item_id: str, body: ToolUpdate):
    """更新工具的描述（abstract / abstract_zh），同时写入 prey/*.json"""
    data, _ = get_data()
    new_zh = (body.abstract_zh or "").strip()
    new_en = (body.abstract or "").strip()
    
    # 找到目标 item
    target = None
    for item in data.get("items", []):
        if item.get("id") == item_id:
            target = item
            break
    
    if not target:
        raise HTTPException(status_code=404, detail="工具不存在")
    
    # 更新 data.json 内存中的值
    if new_zh: target["abstract_zh"] = new_zh
    if new_en: target["abstract"] = new_en
    
    # 保存到 data.json
    with open(DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # 也更新 prey/*.json（如果它的 name/title 匹配）
    prey_dir = BASE_DIR / "prey"
    prey_updated = False
    if prey_dir.exists():
        target_title = (target.get("title") or "").strip()
        for fname in os.listdir(str(prey_dir)):
            if not fname.endswith(".json"): continue
            fpath = os.path.join(str(prey_dir), fname)
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    prey = json.load(f)
                prey_name = (prey.get("name") or prey.get("title") or "").strip()
                if prey_name == target_title:
                    if new_zh: prey["abstract_zh"] = prey.get("abstract_zh", "") or new_zh
                    if new_en: prey["abstract_en"] = prey.get("abstract_en", "") or new_en
                    with open(fpath, 'w', encoding='utf-8') as f:
                        json.dump(prey, f, ensure_ascii=False, indent=2)
                    prey_updated = True
                    break
            except:
                continue
    
    # 重新加载缓存
    load_data()
    
    return {"success": True, "prey_updated": prey_updated, "title": target_title}


@app.get("/api/daily")
def get_daily():
    """获取今日推荐、热门趋势、每日精选"""
    data, _ = get_data()
    return {
        "today_recommends": data.get("today_recommends", []),
        "trending": data.get("trending", []),
        "daily_picks": data.get("daily_picks", []),
        "today_info": data.get("today_info", {}),
        "updated_at": data.get("updated_at", ""),
    }


@app.get("/api/categories")
def get_categories():
    """获取分类统计"""
    data, _ = get_data()
    return data.get("categories", {})


@app.get("/api/sources")
def get_sources():
    """获取来源统计"""
    data, _ = get_data()
    return data.get("sources", {})


@app.get("/api/stats")
def get_stats():
    """获取站点统计"""
    data, _ = get_data()
    items = data.get("items", [])
    return {
        "total": len(items),
        "sources": data.get("sources", {}),
        "regions": data.get("regions", {}),
        "categories": data.get("categories", {}),
        "scenes": data.get("scenes", {}),
        "updated_at": data.get("updated_at", ""),
        "validated_at": data.get("validated_at", ""),
    }


# ═══════════════════════════════════════
# 静态文件托管
# ═══════════════════════════════════════

# 非 API 路由 → 返回静态文件（SPA 兼容）
# 对 /api/ 或 /health 开头的请求，静态文件不拦截
from fastapi.responses import FileResponse
import re

# 静态文件白名单：只有这些路径才从 StaticFiles 返回
@app.get("/{full_path:path}")
async def serve_static(full_path: str):
    # API 路由不经过这里
    if full_path.startswith("api/") or full_path == "health":
        from fastapi.responses import JSONResponse
        return JSONResponse({"error": "not_found"}, status_code=404)
    
    file_path = SITE_DIR / full_path if full_path else SITE_DIR / "index.html"
    if not file_path.exists():
        file_path = SITE_DIR / "index.html"
    if not file_path.exists():
        return JSONResponse({"error": "not_found"}, status_code=404)
    return FileResponse(str(file_path))


# ═══════════════════════════════════════
# 启动入口
# ═══════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    port = int(sys.argv[sys.argv.index("--port") + 1]) if "--port" in sys.argv else 4321
    dev_mode = "--dev" in sys.argv
    host = "0.0.0.0" if not dev_mode else "127.0.0.1"
    
    print(f"  ⚡ AIbounty API Server")
    print(f"  📦 端口: {port} | 模式: {'开发' if dev_mode else '生产'}")
    print(f"  📁 静态文件: {SITE_DIR}")
    print(f"  📊 数据源: {DATA_PATH}")
    
    uvicorn.run(
        "api_server:app",
        host=host,
        port=port,
        reload=dev_mode,
        log_level="info",
    )
