from app.database import SessionLocal
from app.curators import sync_feed

VIDEO_IDS = [
    "g5XHXSOmONk",
]

if __name__ == "__main__":
    db = SessionLocal()
    try:
        total = sync_feed(db, VIDEO_IDS)
        print(f"Done. Total ingested: {total}")
    finally:
        db.close()