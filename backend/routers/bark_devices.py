"""
Bark 推送设备管理（多设备）
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from models import BarkDevice

logger = logging.getLogger(__name__)
router = APIRouter()


# ── schemas ────────────────────────────────────────────────────────────────────

class DeviceIn(BaseModel):
    name: str
    server_url: str = "https://api.day.app"
    device_key: str
    sound: str = ""
    enabled: bool = True


class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    server_url: Optional[str] = None
    device_key: Optional[str] = None   # 为空则不修改
    sound: Optional[str] = None
    enabled: Optional[bool] = None


def _mask_key(key: str) -> str:
    if len(key) <= 8:
        return "***"
    return key[:4] + "***" + key[-4:]


def _serialize(d: BarkDevice) -> dict:
    return {
        "id": d.id,
        "name": d.name,
        "server_url": d.server_url,
        "device_key_masked": _mask_key(d.device_key),
        "sound": d.sound or "",
        "enabled": d.enabled,
        "created_at": d.created_at.isoformat() if d.created_at else None,
    }


# ── endpoints ──────────────────────────────────────────────────────────────────

@router.get("")
def list_devices(db: Session = Depends(get_db)):
    devices = db.query(BarkDevice).order_by(BarkDevice.created_at).all()
    return {"items": [_serialize(d) for d in devices]}


@router.post("", status_code=201)
def create_device(body: DeviceIn, db: Session = Depends(get_db)):
    if not body.name.strip():
        raise HTTPException(400, "名称不能为空")
    if not body.device_key.strip():
        raise HTTPException(400, "Device Key 不能为空")
    from datetime import datetime
    d = BarkDevice(
        name=body.name.strip(),
        server_url=body.server_url.strip() or "https://api.day.app",
        device_key=body.device_key.strip(),
        sound=body.sound.strip(),
        enabled=body.enabled,
        created_at=datetime.utcnow(),
    )
    db.add(d)
    db.commit()
    db.refresh(d)
    return _serialize(d)


@router.put("/{device_id}")
def update_device(device_id: int, body: DeviceUpdate, db: Session = Depends(get_db)):
    d = db.query(BarkDevice).filter(BarkDevice.id == device_id).first()
    if not d:
        raise HTTPException(404, "设备不存在")
    if body.name is not None:
        d.name = body.name.strip()
    if body.server_url is not None:
        d.server_url = body.server_url.strip() or "https://api.day.app"
    if body.device_key:          # 非空才覆盖
        d.device_key = body.device_key.strip()
    if body.sound is not None:
        d.sound = body.sound.strip()
    if body.enabled is not None:
        d.enabled = body.enabled
    db.commit()
    db.refresh(d)
    return _serialize(d)


@router.delete("/{device_id}")
def delete_device(device_id: int, db: Session = Depends(get_db)):
    d = db.query(BarkDevice).filter(BarkDevice.id == device_id).first()
    if not d:
        raise HTTPException(404, "设备不存在")
    db.delete(d)
    db.commit()
    return {"ok": True}


@router.post("/{device_id}/test")
def test_device(device_id: int, db: Session = Depends(get_db)):
    d = db.query(BarkDevice).filter(BarkDevice.id == device_id).first()
    if not d:
        raise HTTPException(404, "设备不存在")
    from services.bark import send as bark_send
    ok = bark_send(
        server_url=d.server_url,
        device_key=d.device_key,
        title="X监控 - 测试通知",
        body=f"设备「{d.name}」推送配置成功！",
        sound=d.sound or "",
    )
    return {"ok": ok, "message": "推送成功" if ok else "推送失败，请检查配置"}
