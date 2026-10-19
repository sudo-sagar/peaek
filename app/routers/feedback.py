from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/api", tags=["feedback"])

MIN_LEN = 3
MAX_LEN = 2000


@router.post("/feedback")
def submit_feedback(payload: schemas.FeedbackCreate, db: Session = Depends(get_db)):
    text = (payload.text or "").strip()

    if len(text) < MIN_LEN:
        raise HTTPException(status_code=400, detail="Feedback is too short")
    if len(text) > MAX_LEN:
        raise HTTPException(status_code=400, detail="Feedback is too long")

    row = models.Feedback(user_id=payload.user_id, text=text)
    db.add(row)
    db.commit()
    db.refresh(row)

    return {"ok": True, "id": row.id}