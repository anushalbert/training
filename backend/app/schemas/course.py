import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.course import CourseStatus, EnrollmentStatus


class CourseCompetencyIn(BaseModel):
    competency: str = Field(min_length=1, max_length=120)
    required_level: int = Field(ge=1, le=5, default=1)


class CourseCreate(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    description: str | None = None
    required_competencies: list[CourseCompetencyIn] = []


class CourseUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: CourseStatus | None = None
    trainer_id: uuid.UUID | None = None


class CourseOut(BaseModel):
    id: uuid.UUID
    title: str
    description: str | None
    trainer_id: uuid.UUID | None
    status: CourseStatus
    created_at: datetime

    class Config:
        from_attributes = True


class CourseMaterialCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    file_url: str


class CourseMaterialOut(BaseModel):
    id: uuid.UUID
    course_id: uuid.UUID
    title: str
    file_url: str
    uploaded_by: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True


class EnrollmentOut(BaseModel):
    id: uuid.UUID
    course_id: uuid.UUID
    trainee_id: uuid.UUID
    status: EnrollmentStatus
    enrolled_at: datetime

    class Config:
        from_attributes = True


class TrainerSuggestion(BaseModel):
    trainer_id: uuid.UUID
    full_name: str
    email: str
    match_score: float
    matched_competencies: list[str]
