import uuid

from pydantic import BaseModel, Field

# --- Import payload: mirrors the structured course-content JSON format exactly,
# so a file like "dynamic-meteorology-imtc.json" can be uploaded as-is. ---


class ContentBlockImport(BaseModel):
    type: str = Field(pattern="^(text|formula|example)$")
    heading: str | None = None
    body: str | None = None
    label: str | None = None
    expression: str | None = None
    explanation: str | None = None


class NoteAnchorImport(BaseModel):
    anchor_text: str | None = None
    suggested_note_prompt: str | None = None


class LessonImport(BaseModel):
    lesson_id: str | None = None
    title: str
    content_blocks: list[ContentBlockImport] = []
    note_anchors: list[NoteAnchorImport] = []


class WeekImport(BaseModel):
    week_number: int
    title: str
    overview: str | None = None
    estimated_minutes: int | None = None
    lessons: list[LessonImport] = []
    completion_criteria: list[str] = []


class CourseMetaImport(BaseModel):
    subject: str
    source_pdf: str | None = None
    source_url: str | None = None
    author: str | None = None
    tier: str | None = None
    difficulty: str | None = None
    total_weeks: int | None = None
    estimated_hours: float | None = None
    prerequisites: list[str] = []


class QAItemImport(BaseModel):
    question: str
    answer: str
    source_week: int | None = None
    difficulty: str | None = None


class TestQuestionImport(BaseModel):
    question: str
    type: str = Field(pattern="^(mcq|true_false|fill_in_blank|short_answer)$")
    options: list[str] | None = None
    correct_answer: str
    source_week: int | None = None
    difficulty: str | None = None


class CourseContentImport(BaseModel):
    course_meta: CourseMetaImport
    weeks: list[WeekImport] = []
    ai_qa_concept_clarification: list[QAItemImport] = []
    ai_test_questions: list[TestQuestionImport] = []
    # if true, ai_test_questions are built into a real Assessment trainees can take
    create_assessment: bool = True


class ImportResult(BaseModel):
    course_id: uuid.UUID
    weeks_created: int
    lessons_created: int
    qa_items_created: int
    assessment_id: uuid.UUID | None = None
    questions_created: int
    skipped_questions: list[str] = []


# --- Read models: what the trainee-facing lesson viewer fetches. ---


class ContentBlockOut(BaseModel):
    id: uuid.UUID
    order_index: int
    block_type: str
    heading: str | None = None
    body: str | None = None
    label: str | None = None
    expression: str | None = None
    explanation: str | None = None

    class Config:
        from_attributes = True


class NoteAnchorOut(BaseModel):
    id: uuid.UUID
    anchor_text: str | None = None
    suggested_note_prompt: str | None = None

    class Config:
        from_attributes = True


class LessonOut(BaseModel):
    id: uuid.UUID
    lesson_key: str | None = None
    title: str
    order_index: int
    content_blocks: list[ContentBlockOut] = []
    note_anchors: list[NoteAnchorOut] = []

    class Config:
        from_attributes = True


class CompletionCriterionOut(BaseModel):
    id: uuid.UUID
    criterion_text: str
    order_index: int

    class Config:
        from_attributes = True


class WeekOut(BaseModel):
    id: uuid.UUID
    week_number: int
    title: str
    overview: str | None = None
    estimated_minutes: int | None = None
    lessons: list[LessonOut] = []
    completion_criteria: list[CompletionCriterionOut] = []

    class Config:
        from_attributes = True


class QAItemOut(BaseModel):
    id: uuid.UUID
    question: str
    answer: str
    source_week: int | None = None
    difficulty: str | None = None

    class Config:
        from_attributes = True
