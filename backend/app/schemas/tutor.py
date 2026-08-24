import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class TutorMessageIn(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class TutorMessage(BaseModel):
    role: str
    content: str
    timestamp: str | None = None


class TutorChatOut(BaseModel):
    lesson_id: uuid.UUID
    messages: list[TutorMessage]


class TutorConversationOut(BaseModel):
    lesson_id: uuid.UUID
    messages: list[TutorMessage]
    updated_at: datetime | None = None
