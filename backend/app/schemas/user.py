import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole


class UserSignup(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: UserRole = UserRole.trainee


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: uuid.UUID
    full_name: str
    email: EmailStr
    role: UserRole
    is_approved: bool
    is_active: bool
    bio: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class UserProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=150)
    bio: str | None = None


class TrainerCompetencyIn(BaseModel):
    competency: str = Field(min_length=1, max_length=120)
    proficiency_level: int = Field(ge=1, le=5)


class TrainerCompetencyOut(TrainerCompetencyIn):
    id: uuid.UUID
    trainer_id: uuid.UUID

    class Config:
        from_attributes = True
