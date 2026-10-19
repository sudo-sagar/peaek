from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.database import get_db
from app import models

router = APIRouter(prefix="/api/users", tags=["users"])


@router.post("/ping")
def ping_user(payload: dict, db: Session = Depends(get_db)):
    """Called on every app open. Registers or updates a device."""
    device_id = (payload or {}).get("device_id")
    app_version = (payload or {}).get("app_version")

    if not device_id:
        raise HTTPException(status_code=400, detail="device_id required")

    existing = db.query(models.UserDevice).filter_by(device_id=device_id).first()
    now = datetime.utcnow()

    if existing:
        existing.last_seen = now
        if app_version:
            existing.app_version = app_version
    else:
        db.add(models.UserDevice(
            device_id=device_id,
            app_version=app_version,
            first_seen=now,
            last_seen=now,
        ))

    db.commit()
    return {"ok": True}


@router.get("/count")
def user_count(db: Session = Depends(get_db)):
    """Total unique devices + active in last 24h."""
    cutoff = datetime.utcnow() - timedelta(hours=24)

    total = db.query(models.UserDevice).count()
    active_24h = (
        db.query(models.UserDevice)
        .filter(models.UserDevice.last_seen >= cutoff)
        .count()
    )
    return {"total": total, "active_24h": active_24h}