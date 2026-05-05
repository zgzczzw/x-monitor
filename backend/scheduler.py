"""
定时采集调度器 —— 监控 watch_users 的新推文，发 Bark 通知
"""
import logging
from datetime import datetime
from collections import deque

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler(timezone="UTC")

DEFAULT_INTERVAL = 5  # 分钟

_status = {
    "last_run": None,
    "last_result": None,
    "running": False,
    "total_runs": 0,
}
_history: deque = deque(maxlen=50)


def get_status() -> dict:
    return {
        **_status,
        "next_run": _next_run_time(),
        "interval_minutes": _current_interval(),
    }


def get_history() -> list:
    return list(reversed(_history))


def _next_run_time():
    job = scheduler.get_job("collect_tweets")
    if job and job.next_run_time:
        return job.next_run_time.isoformat()
    return None


def _current_interval() -> int:
    from database import SessionLocal
    from models import Setting
    db = SessionLocal()
    try:
        row = db.query(Setting).filter(Setting.key == "collect_interval").first()
        return int(row.value) if row and row.value.isdigit() else DEFAULT_INTERVAL
    finally:
        db.close()


def _get_setting(db, key: str) -> str:
    from models import Setting
    row = db.query(Setting).filter(Setting.key == key).first()
    return row.value if row else ""


def _reschedule(interval: int):
    """动态更新采集间隔"""
    scheduler.reschedule_job(
        "collect_tweets",
        trigger=IntervalTrigger(minutes=interval),
    )
    logger.info(f"采集间隔已更新为 {interval} 分钟")


async def run_collection():
    if _status["running"]:
        return {"skipped": True, "reason": "already_running"}

    _status["running"] = True
    _status["total_runs"] += 1
    start = datetime.utcnow()
    _status["last_run"] = start.isoformat()

    log_entry = {
        "id": _status["total_runs"],
        "started_at": start.isoformat(),
        "finished_at": None,
        "duration_s": None,
        "status": "running",
        "result": None,
    }
    _history.append(log_entry)

    try:
        from database import SessionLocal
        from models import Tweet, BarkDevice, Setting
        from collectors.twitter import fetch_new_tweets
        from services.bark import send as bark_send
        from services.translation import translate

        db = SessionLocal()
        try:
            api_key = _get_setting(db, "twitter_api_key")
            watch_raw = _get_setting(db, "twitter_watch_users")
            watch_users = [u.strip().lstrip("@") for u in watch_raw.split(",") if u.strip()]

            if not api_key or not watch_users:
                result = {"saved": 0, "skipped": 0, "users": watch_users}
                _status["last_result"] = result
                log_entry["result"] = result
                log_entry["status"] = "success"
                return result

            saved = skipped = 0
            new_tweets = []

            for username in watch_users:
                # 读取该用户上次已知最新 tweet id
                since_key = f"last_tweet_id_{username.lower()}"
                since_id = _get_setting(db, since_key)
                is_first_run = not since_id  # 首次采集该用户，不发推送

                tweets = fetch_new_tweets(api_key, username, since_id=since_id)

                for tw in tweets:
                    exists = db.query(Tweet.id).filter(Tweet.source_id == tw["source_id"]).first()
                    if exists:
                        skipped += 1
                        continue
                    # 翻译
                    content_zh = translate(tw["content"])
                    tw["content_zh"] = content_zh
                    t = Tweet(
                        author=tw["author"],
                        content=tw["content"],
                        content_zh=content_zh or None,
                        url=tw["url"],
                        source_id=tw["source_id"],
                        tweeted_at=tw["tweeted_at"],
                        saved_at=datetime.utcnow(),
                    )
                    db.add(t)
                    saved += 1
                    # 首次采集只入库，不推送
                    if not is_first_run:
                        new_tweets.append(tw)

                # 更新该用户最新 tweet id（取最大值，防止 API 返回乱序）
                if tweets:
                    latest_id = max(tweets, key=lambda t: int(t["tweet_id"]))["tweet_id"]
                    row = db.query(Setting).filter(Setting.key == since_key).first()
                    if row:
                        row.value = latest_id
                    else:
                        db.add(Setting(key=since_key, value=latest_id))
                    if is_first_run:
                        logger.info(f"@{username} 首次采集，初始化 since_id={latest_id}，不发推送")

            db.commit()

            # Bark 推送
            if new_tweets:
                devices = db.query(BarkDevice).filter(BarkDevice.enabled == True).all()
                for tw in new_tweets:
                    zh = tw.get("content_zh", "")
                    if zh:
                        body = f"{tw['content'][:150]}\n\n🀄 {zh[:150]}"
                    else:
                        body = tw["content"][:200]
                    for dev in devices:
                        bark_send(
                            server_url=dev.server_url,
                            device_key=dev.device_key,
                            title=f"@{tw['author']} 发了新推文",
                            body=body,
                            url=tw.get("url", ""),
                            sound=dev.sound or "",
                        )

            result = {"saved": saved, "skipped": skipped, "users": watch_users, "pushed": len(new_tweets)}
            _status["last_result"] = result
            log_entry["result"] = result
            log_entry["status"] = "success"
            logger.info(f"采集完成: {result}")
            return result

        finally:
            db.close()

    except Exception as e:
        logger.error(f"采集异常: {e}", exc_info=True)
        err = {"error": str(e)}
        _status["last_result"] = err
        log_entry["result"] = err
        log_entry["status"] = "error"
        return err
    finally:
        _status["running"] = False
        finished = datetime.utcnow()
        log_entry["finished_at"] = finished.isoformat()
        log_entry["duration_s"] = round((finished - start).total_seconds(), 1)


def start():
    interval = DEFAULT_INTERVAL
    try:
        interval = _current_interval()
    except Exception:
        pass
    scheduler.add_job(
        run_collection,
        trigger=IntervalTrigger(minutes=interval),
        id="collect_tweets",
        replace_existing=True,
        max_instances=1,
    )
    scheduler.start()
    logger.info(f"调度器启动，间隔 {interval} 分钟")


def stop():
    if scheduler.running:
        scheduler.shutdown(wait=False)
