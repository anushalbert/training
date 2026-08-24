import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class AnnouncementCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    message: str = Field(min_length=1)


class AnnouncementOut(BaseModel):
    id: uuid.UUID
    title: str
    message: str
    created_by: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True
