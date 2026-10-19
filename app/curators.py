from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app import models
from app.youtube import get_trending_videos, fetch_top_comment

MIN_COMMENT_LENGTH = 15


def is_worth_keeping(text):
    if not text:
        return False
    stripped = text.strip()
    if len(stripped) < MIN_COMMENT_LENGTH:
        return False
    non_emoji = "".join(ch for ch in stripped if ch.isalnum())
    if len(non_emoji) < 5:
        return False
    return True


def refresh_top_comments(db: Session, region="IN", max_per_category=5, expiry_hours=24):
    now = datetime.utcnow()
    cutoff = now - timedelta(hours=expiry_hours)

    videos = get_trending_videos(region=region, max_per_category=max_per_category)
    print(f"Total trending videos: {len(videos)}")

    inserted = 0
    updated = 0
    skipped = 0

    for video in videos:
        top = fetch_top_comment(video["video_id"])
        if not top or not is_worth_keeping(top["comment_text"]):
            skipped += 1
            continue

        existing = (
            db.query(models.TopComment)
            .filter_by(video_id=video["video_id"])
            .first()
        )
        if existing:
            existing.comment_text = top["comment_text"]
            existing.comment_author = top["comment_author"]
            existing.comment_likes = top["comment_likes"]
            existing.comment_reply_count = top["comment_reply_count"]
            existing.video_category = video["category_id"]
            existing.last_seen = now
            updated += 1
        else:
            db.add(models.TopComment(
                video_id=video["video_id"],
                video_category=video["category_id"],
                comment_text=top["comment_text"],
                comment_author=top["comment_author"],
                comment_likes=top["comment_likes"],
                comment_reply_count=top["comment_reply_count"],
                last_seen=now,
            ))
            inserted += 1

        db.commit()

    deleted = (
        db.query(models.TopComment)
        .filter(models.TopComment.last_seen < cutoff)
        .delete(synchronize_session=False)
    )
    db.commit()

    print(f"Done. inserted={inserted} updated={updated} skipped={skipped} deleted={deleted}")
    return inserted + updated