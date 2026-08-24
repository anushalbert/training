import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class FeedbackCreate(BaseModel):
    course_id: uuid.UUID
    rating: int = Field(ge=1, le=5)
    comments: str | None = None


class FeedbackOut(BaseModel):
    id: uuid.UUID
    course_id: uuid.UUID
    trainee_id: uuid.UUID
    rating: int
    comments: str | None
    created_at: datetime

    class Config:
        from_attributes = True
