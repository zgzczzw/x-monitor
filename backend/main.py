import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy import text

from database import engine, Base

DIST_DIR = Path(__file__).parent.parent / "frontend" / "dist"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)


def _migrate():
    with engine.connect() as conn:
        # tweets 表（新）
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS tweets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                author VARCHAR NOT NULL,
                content VARCHAR NOT NULL,
                content_zh VARCHAR,
                url VARCHAR,
                source_id VARCHAR NOT NULL UNIQUE,
                tweeted_at DATETIME,
                saved_at DATETIME
            )
        """))
        # 旧表补字段
        try:
            conn.execute(text("ALTER TABLE tweets ADD COLUMN content_zh VARCHAR"))
            conn.commit()
        except Exception:
            pass
        # bark_devices 表
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS bark_devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR NOT NULL,
                server_url VARCHAR NOT NULL DEFAULT 'https://api.day.app',
                device_key VARCHAR NOT NULL,
                sound VARCHAR DEFAULT '',
                enabled BOOLEAN DEFAULT 1,
                created_at DATETIME
            )
        """))
        # settings 表
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS settings (
                key VARCHAR PRIMARY KEY,
                value VARCHAR NOT NULL DEFAULT ''
            )
        """))
        conn.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    _migrate()

    import scheduler
    scheduler.start()

    yield

    scheduler.stop()


app = FastAPI(title="X Monitor API", lifespan=lifespan)

from routers import settings, bark_devices
from routers.tweets import router as tweets_router

app.include_router(settings.router, prefix="/api/settings", tags=["settings"])
app.include_router(bark_devices.router, prefix="/api/bark-devices", tags=["bark-devices"])
app.include_router(tweets_router, prefix="/api/tweets", tags=["tweets"])


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/collect/trigger")
async def trigger():
    import scheduler as sched
    if sched._status["running"]:
        return {"started": False, "message": "采集中，请稍候"}
    import asyncio
    asyncio.create_task(sched.run_collection())
    return {"started": True}


@app.get("/api/collect/status")
def collect_status():
    import scheduler as sched
    return sched.get_status()


@app.get("/api/collect/history")
def collect_history():
    import scheduler as sched
    return {"items": sched.get_history()}


# 静态文件（Vue 构建产物）
if DIST_DIR.exists():
    app.mount("/assets", StaticFiles(directory=DIST_DIR / "assets"), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa_fallback(full_path: str):
        # API 路由已优先匹配，这里只处理前端路由
        return FileResponse(DIST_DIR / "index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=13002)
