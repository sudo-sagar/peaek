import threading
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from app.database import Base, engine, SessionLocal
from app.routers import cards, feedback, users
from app.curators import refresh_top_comments

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Peaek", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cards.router)
app.include_router(feedback.router)
app.include_router(users.router)


scheduler = BackgroundScheduler()


def run_refresh(label):
    print(f"[{label}] refresh starting...")
    db = SessionLocal()
    try:
        count = refresh_top_comments(db, region="IN", max_per_category=5)
        print(f"[{label}] refresh done: {count} cards")
    except Exception as e:
        print(f"[{label}] refresh failed: {e}")
    finally:
        db.close()


@scheduler.scheduled_job("interval", hours=6, id="refresh_job")
def scheduled_refresh():
    run_refresh("Scheduled")


@app.on_event("startup")
def start_scheduler():
    threading.Thread(target=run_refresh, args=("Startup",), daemon=True).start()
    scheduler.start()
    print("Scheduler started. Refresh every 6 hours.")


@app.on_event("shutdown")
def stop_scheduler():
    scheduler.shutdown()


@app.get("/")
def root():
    return {"status": "ok", "app": "Peaek"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/admin/refresh-cards")
def refresh_cards_endpoint(region: str = "IN", max_per_category: int = 3):
    db = SessionLocal()
    try:
        count = refresh_top_comments(db, region=region, max_per_category=max_per_category)
        return {"ingested": count}
    finally:
        db.close()