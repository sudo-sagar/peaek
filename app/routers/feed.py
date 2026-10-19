from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["feed"])

# Feed logic replaced by app/routers/cards.py