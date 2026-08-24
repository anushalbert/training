import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class LessonCompleteOut(BaseModel):
    lesson_id: uuid.UUID
    completed_at: datetime


class WeekProgress(BaseModel):
    week_number: int
    week_id: uuid.UUID
    total_lessons: int
    completed_lessons: int
    lessons_done: bool
    quiz_required: bool  # False if the week has no auto-gradable questions to gate on
    quiz_passed: bool
    unlocked: bool
    best_score: float | None = None
    attempts: int = 0


class CourseProgress(BaseModel):
    course_id: uuid.UUID
    total_lessons: int
    completed_lessons: int
    percent: float
    completed_lesson_ids: list[uuid.UUID]
    weeks: list[WeekProgress]


# --- Quiz ---


class QuizQuestionOut(BaseModel):
    id: uuid.UUID
    question_type: str
    question_text: str
    option_a: str | None = None
    option_b: str | None = None
    option_c: str | None = None
    option_d: str | None = None

    class Config:
        from_attributes = True


class WeekQuizOut(BaseModel):
    week_id: uuid.UUID
    week_number: int
    questions: list[QuizQuestionOut]
    passing_threshold: float = 70.0


class QuizSubmitIn(BaseModel):
    answers: dict[uuid.UUID, str] = Field(description="question_id -> answer (letter for mcq/true_false, text otherwise)")


class QuizResultOut(BaseModel):
    attempt_id: uuid.UUID
    score: float
    passed: bool
    correct_count: int
    total_auto_gradable: int
    short_answer_flagged: list[uuid.UUID] = []
    next_week_unlocked: bool


# --- Notes ---


class NoteCreate(BaseModel):
    anchor_text: str | None = None
    note_text: str = Field(min_length=1)


class NoteOut(BaseModel):
    id: uuid.UUID
    lesson_id: uuid.UUID
    anchor_text: str | None = None
    note_text: str
    created_at: datetime

    class Config:
        from_attributes = True
