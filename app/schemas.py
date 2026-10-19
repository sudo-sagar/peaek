from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class TopCommentOut(BaseModel):
    id: int
    video_id: str
    video_category: Optional[str]
    comment_text: str
    comment_author: Optional[str]
    comment_likes: int
    comment_reply_count: int
    fetched_at: datetime

    class Config:
        from_attributes = True


class FeedbackCreate(BaseModel):
    user_id: Optional[str] = None
    text: str