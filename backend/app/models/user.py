import uuid

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, SmallInteger, Enum, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base
import enum


class UserRole(str, enum.Enum):
    trainee = "trainee"
    trainer = "trainer"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(String(150), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole, name="user_role"), nullable=False, default=UserRole.trainee)
    is_approved = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    bio = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    competencies = relationship("TrainerCompetency", back_populates="trainer", cascade="all, delete-orphan")
    courses_taught = relationship("Course", back_populates="trainer")
    enrollments = relationship("Enrollment", back_populates="trainee", cascade="all, delete-orphan")


class TrainerCompetency(Base):
    __tablename__ = "trainer_competencies"
    __table_args__ = (UniqueConstraint("trainer_id", "competency", name="uq_trainer_competency"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trainer_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    competency = Column(String(120), nullable=False)
    proficiency_level = Column(SmallInteger, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    trainer = relationship("User", back_populates="competencies")
