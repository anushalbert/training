import uuid
from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.models.assessment import QuestionType


class QuestionIn(BaseModel):
    question_type: QuestionType = QuestionType.mcq
    question_text: str = Field(min_length=1)
    option_a: str | None = None
    option_b: str | None = None
    option_c: str | None = None
    option_d: str | None = None
    # mcq/true_false: a letter A-D matching one of the supplied options.
    # fill_in_blank/short_answer: the expected free-text answer.
    correct_answer: str = Field(min_length=1)
    competency_tag: str | None = None

    @model_validator(mode="after")
    def _validate_options(self):
        if self.question_type in (QuestionType.mcq, QuestionType.true_false):
            options = [self.option_a, self.option_b, self.option_c, self.option_d]
            present = [o for o in options if o is not None]
            if len(present) < 2:
                raise ValueError("mcq/true_false questions need at least option_a and option_b")
            valid_letters = "ABCD"[: len(options)]
            if self.correct_answer.upper() not in valid_letters or options[ord(self.correct_answer.upper()) - 65] is None:
                raise ValueError("correct_answer must be a letter pointing at a supplied option")
            self.correct_answer = self.correct_answer.upper()
        return self


class QuestionOut(BaseModel):
    id: uuid.UUID
    question_type: QuestionType
    question_text: str
    option_a: str | None = None
    option_b: str | None = None
    option_c: str | None = None
    option_d: str | None = None
    competency_tag: str | None = None
    # correct_answer intentionally omitted when serving to trainees taking the test

    class Config:
        from_attributes = True


class QuestionOutWithAnswer(QuestionOut):
    correct_answer: str


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
    answers: dict[uuid.UUID, str] = Field(description="question_id -> answer (option letter, or free text)")


class SubmissionOut(BaseModel):
    id: uuid.UUID
    assessment_id: uuid.UUID
    trainee_id: uuid.UUID
    score: float
    total_questions: int
    submitted_at: datetime

    class Config:
        from_attributes = True
