import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class QuestionIn(BaseModel):
    question_text: str = Field(min_length=1)
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_option: str = Field(pattern="^[ABCD]$")
    competency_tag: str | None = None


class QuestionOut(BaseModel):
    id: uuid.UUID
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    competency_tag: str | None = None
    # correct_option intentionally omitted when serving to trainees taking the test

    class Config:
        from_attributes = True


class QuestionOutWithAnswer(QuestionOut):
    correct_option: str


class AssessmentCreate(BaseModel):
    course_id: uuid.UUID
    title: str = Field(min_length=2, max_length=200)
    questions: list[QuestionIn] = []


class AssessmentOut(BaseModel):
    id: uuid.UUID
    course_id: uuid.UUID
    title: str
    created_by: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True


class AssessmentDetail(AssessmentOut):
    questions: list[QuestionOut]


class SubmissionCreate(BaseModel):
    answers: dict[uuid.UUID, str] = Field(description="question_id -> selected option (A/B/C/D)")


class SubmissionOut(BaseModel):
    id: uuid.UUID
    assessment_id: uuid.UUID
    trainee_id: uuid.UUID
    score: float
    total_questions: int
    submitted_at: datetime

    class Config:
        from_attributes = True
