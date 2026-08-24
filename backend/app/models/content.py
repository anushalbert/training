import uuid

from sqlalchemy import Column, String, Text, Integer, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class CourseWeek(Base):
    __tablename__ = "course_weeks"
    __table_args__ = (UniqueConstraint("course_id", "week_number", name="uq_course_week"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    week_number = Column(Integer, nullable=False)
    title = Column(String(200), nullable=False)
    overview = Column(Text, nullable=True)
    estimated_minutes = Column(Integer, nullable=True)

    course = relationship("Course", back_populates="weeks")
    lessons = relationship("Lesson", back_populates="week", cascade="all, delete-orphan", order_by="Lesson.order_index")
    completion_criteria = relationship(
        "WeekCompletionCriterion", back_populates="week", cascade="all, delete-orphan", order_by="WeekCompletionCriterion.order_index"
    )


class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    week_id = Column(UUID(as_uuid=True), ForeignKey("course_weeks.id", ondelete="CASCADE"), nullable=False)
    lesson_key = Column(String(50), nullable=True)
    title = Column(String(200), nullable=False)
    order_index = Column(Integer, nullable=False, default=0)

    week = relationship("CourseWeek", back_populates="lessons")
    content_blocks = relationship(
        "LessonContentBlock", back_populates="lesson", cascade="all, delete-orphan", order_by="LessonContentBlock.order_index"
    )
    note_anchors = relationship("LessonNoteAnchor", back_populates="lesson", cascade="all, delete-orphan")


class LessonContentBlock(Base):
    __tablename__ = "lesson_content_blocks"
    __table_args__ = (CheckConstraint("block_type IN ('text', 'formula', 'example')", name="ck_block_type"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lesson_id = Column(UUID(as_uuid=True), ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False)
    order_index = Column(Integer, nullable=False, default=0)
    block_type = Column(String(20), nullable=False)
    heading = Column(String(200), nullable=True)
    body = Column(Text, nullable=True)
    label = Column(String(200), nullable=True)
    expression = Column(Text, nullable=True)
    explanation = Column(Text, nullable=True)

    lesson = relationship("Lesson", back_populates="content_blocks")


class LessonNoteAnchor(Base):
    __tablename__ = "lesson_note_anchors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lesson_id = Column(UUID(as_uuid=True), ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False)
    anchor_text = Column(Text, nullable=True)
    suggested_note_prompt = Column(Text, nullable=True)

    lesson = relationship("Lesson", back_populates="note_anchors")


class WeekCompletionCriterion(Base):
    __tablename__ = "week_completion_criteria"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    week_id = Column(UUID(as_uuid=True), ForeignKey("course_weeks.id", ondelete="CASCADE"), nullable=False)
    criterion_text = Column(Text, nullable=False)
    order_index = Column(Integer, nullable=False, default=0)

    week = relationship("CourseWeek", back_populates="completion_criteria")


class CourseQAItem(Base):
    __tablename__ = "course_qa_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    source_week = Column(Integer, nullable=True)
    difficulty = Column(String(20), nullable=True)

    course = relationship("Course", back_populates="qa_items")
