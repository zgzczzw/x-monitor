import logging
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import Setting

logger = logging.getLogger(__name__)
router = APIRouter()


def _get(db: Session, key: str, default: str = "") -> str:
    row = db.query(Setting).filter(Setting.key == key).first()
    return row.value if row else default


def _set(db: Session, key: str, value: str) -> None:
    row = db.query(Setting).filter(Setting.key == key).first()
    if row:
        row.value = value
    else:
        db.add(Setting(key=key, value=value))
    db.commit()


class TwitterSettingsOut(BaseModel):
    api_key_configured: bool
    api_key_masked: str
    watch_users: str


class TwitterSettingsIn(BaseModel):
    api_key: str = ""
    watch_users: str = ""


@router.get("/twitter", response_model=TwitterSettingsOut)
def get_twitter_settings(db: Session = Depends(get_db)):
    key = _get(db, "twitter_api_key")
    masked = (key[:6] + "***") if key else ""
    return TwitterSettingsOut(
        api_key_configured=bool(key),
        api_key_masked=masked,
        watch_users=_get(db, "twitter_watch_users"),
    )


@router.put("/twitter")
def save_twitter_settings(body: TwitterSettingsIn, db: Session = Depends(get_db)):
    if body.api_key:
        _set(db, "twitter_api_key", body.api_key.strip())
    _set(db, "twitter_watch_users", body.watch_users.strip())
    return {"ok": True}


@router.delete("/twitter/api-key")
def clear_twitter_api_key(db: Session = Depends(get_db)):
    _set(db, "twitter_api_key", "")
    return {"ok": True}


# ── 时区设置 ──────────────────────────────────────────────────────────────────

class TimezoneSettingsOut(BaseModel):
    timezone: str


class TimezoneSettingsIn(BaseModel):
    timezone: str


@router.get("/timezone", response_model=TimezoneSettingsOut)
def get_timezone(db: Session = Depends(get_db)):
    return TimezoneSettingsOut(timezone=_get(db, "timezone", "Asia/Shanghai"))


@router.put("/timezone")
def save_timezone(body: TimezoneSettingsIn, db: Session = Depends(get_db)):
    _set(db, "timezone", body.timezone.strip())
    return {"ok": True}


# ── 采集间隔 ──────────────────────────────────────────────────────────────────

class IntervalOut(BaseModel):
    interval_minutes: int


class IntervalIn(BaseModel):
    interval_minutes: int


@router.get("/interval", response_model=IntervalOut)
def get_interval(db: Session = Depends(get_db)):
    val = _get(db, "collect_interval", "5")
    return IntervalOut(interval_minutes=int(val) if val.isdigit() else 5)


@router.put("/interval")
def save_interval(body: IntervalIn, db: Session = Depends(get_db)):
    minutes = max(1, min(body.interval_minutes, 60))
    _set(db, "collect_interval", str(minutes))
    # 动态更新调度器
    try:
        import scheduler as sched
        sched._reschedule(minutes)
    except Exception:
        pass
    return {"ok": True, "interval_minutes": minutes}
