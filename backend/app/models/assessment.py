import uuid
import enum

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, Numeric, UniqueConstraint, Enum, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class QuestionType(str, enum.Enum):
    mcq = "mcq"
    true_false = "true_false"
    fill_in_blank = "fill_in_blank"
    short_answer = "short_answer"


class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    course = relationship("Course", back_populates="assessments")
    questions = relationship("AssessmentQuestion", back_populates="assessment", cascade="all, delete-orphan")
    submissions = relationship("AssessmentSubmission", back_populates="assessment", cascade="all, delete-orphan")


class AssessmentQuestion(Base):
    __tablename__ = "assessment_questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_id = Column(UUID(as_uuid=True), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False)
    question_type = Column(Enum(QuestionType, name="question_type"), nullable=False, default=QuestionType.mcq)
    question_text = Column(Text, nullable=False)
    option_a = Column(String(500), nullable=True)
    option_b = Column(String(500), nullable=True)
    option_c = Column(String(500), nullable=True)
    option_d = Column(String(500), nullable=True)
    # mcq/true_false: correct option letter (A-D). fill_in_blank/short_answer: expected free text.
    correct_answer = Column(String(500), nullable=False)
    competency_tag = Column(String(120), nullable=True)
    # which course week this question gates (from ai_test_questions.source_week on import)
    source_week = Column(Integer, nullable=True)

    assessment = relationship("Assessment", back_populates="questions")


class AssessmentSubmission(Base):
    __tablename__ = "assessment_submissions"
    __table_args__ = (UniqueConstraint("assessment_id", "trainee_id", name="uq_assessment_trainee"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_id = Column(UUID(as_uuid=True), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False)
    trainee_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    score = Column(Numeric(5, 2), nullable=False, default=0)
    total_questions = Column(Integer, nullable=False, default=0)
    answers = Column(JSONB, nullable=False, default=dict)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())

    assessment = relationship("Assessment", back_populates="submissions")
