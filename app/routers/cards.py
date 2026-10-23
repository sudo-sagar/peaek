from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/api", tags=["cards"])

CATEGORY_MAP = {
    "1": "Film & Animation",
    "2": "Autos & Vehicles",
    "10": "Music",
    "15": "Pets & Animals",
    "17": "Sports",
    "18": "Short Movies",
    "19": "Travel & Events",
    "20": "Gaming",
    "22": "People & Blogs",
    "23": "Comedy",
    "24": "Entertainment",
    "25": "News & Politics",
    "26": "Howto & Style",
    "27": "Education",
    "28": "Science & Technology"
}

CATEGORY_ORDER = ["23", "24", "20", "17", "10", "1", "2", "15", "18", "19", "22", "25", "26", "27", "28"]

@router.get("/cards", response_model=List[schemas.TopCommentOut])
def get_cards(
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Flat list, optionally filtered by category."""
    q = db.query(models.TopComment)
    if category and category in CATEGORY_MAP:
        q = q.filter(models.TopComment.video_category == category)
    return (
        q.order_by(models.TopComment.comment_likes.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


@router.get("/cards/by-category")
def get_cards_by_category(
    per_category: int = Query(3, ge=1, le=10),
    db: Session = Depends(get_db),
):
    """Top N cards per category. Used for the 'All' view."""
    result = []
    for cat_id in CATEGORY_ORDER:
        top = (
            db.query(models.TopComment)
            .filter(models.TopComment.video_category == cat_id)
            .order_by(models.TopComment.comment_likes.desc())
            .limit(per_category)
            .all()
        )
        if not top:
            continue
        result.append({
            "category_id": cat_id,
            "category_name": CATEGORY_MAP[cat_id],
            "cards": [
                schemas.TopCommentOut.model_validate(c).model_dump()
                for c in top
            ],
        })
    return result