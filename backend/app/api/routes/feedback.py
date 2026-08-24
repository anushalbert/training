import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.course import Course, Enrollment
from app.models.feedback import Feedback
from app.models.user import User, UserRole
from app.schemas.feedback import FeedbackCreate, FeedbackOut
from app.api.deps import get_current_user, require_trainer_or_admin

router = APIRouter(prefix="/api/feedback", tags=["feedback"])


@router.post("", response_model=FeedbackOut, status_code=status.HTTP_201_CREATED)
def submit_feedback(
    payload: FeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != UserRole.trainee:
        raise HTTPException(status_code=403, detail="Only trainees can submit feedback")

    enrolled = (
        db.query(Enrollment)
        .filter(Enrollment.course_id == payload.course_id, Enrollment.trainee_id == current_user.id)
        .first()
    )
    if not enrolled:
        raise HTTPException(status_code=403, detail="Enroll in this course to leave feedback")

    existing = (
        db.query(Feedback)
        .filter(Feedback.course_id == payload.course_id, Feedback.trainee_id == current_user.id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Feedback already submitted for this course")

    feedback = Feedback(
        course_id=payload.course_id,
        trainee_id=current_user.id,
        rating=payload.rating,
        comments=payload.comments,
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback


@router.get("/course/{course_id}", response_model=list[FeedbackOut])
def list_feedback_for_course(
    course_id: uuid.UUID,
    current_user: User = Depends(require_trainer_or_admin),
    db: Session = Depends(get_db),
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if current_user.role == UserRole.trainer and course.trainer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your course")
    return db.query(Feedback).filter(Feedback.course_id == course_id).all()
