import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.models.course import Course, Enrollment
from app.models.assessment import AssessmentSubmission
from app.models.user import User, UserRole
from app.schemas.user import UserOut
from app.schemas.course import TrainerSuggestion
from app.api.deps import require_admin
from app.services.competency import suggest_trainers_for_course

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/users/pending", response_model=list[UserOut])
def list_pending_users(current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    return db.query(User).filter(User.is_approved.is_(False)).all()


@router.get("/users", response_model=list[UserOut])
def list_all_users(current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    return db.query(User).order_by(User.created_at.desc()).all()


@router.patch("/users/{user_id}/approve", response_model=UserOut)
def approve_user(user_id: uuid.UUID, current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_approved = True
    db.commit()
    db.refresh(user)
    return user


@router.patch("/users/{user_id}/deactivate", response_model=UserOut)
def deactivate_user(user_id: uuid.UUID, current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")
    user.is_active = False
    db.commit()
    db.refresh(user)
    return user


@router.get("/courses/{course_id}/suggest-trainers", response_model=list[TrainerSuggestion])
def suggest_trainers(course_id: uuid.UUID, current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    matches = suggest_trainers_for_course(db, course_id)
    return [
        TrainerSuggestion(
            trainer_id=m.trainer.id,
            full_name=m.trainer.full_name,
            email=m.trainer.email,
            match_score=m.match_score,
            matched_competencies=m.matched_competencies,
        )
        for m in matches
    ]


@router.patch("/courses/{course_id}/assign-trainer/{trainer_id}")
def assign_trainer(
    course_id: uuid.UUID,
    trainer_id: uuid.UUID,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    trainer = db.query(User).filter(User.id == trainer_id, User.role == UserRole.trainer).first()
    if not trainer:
        raise HTTPException(status_code=404, detail="Trainer not found")

    course.trainer_id = trainer.id
    db.commit()
    return {"course_id": str(course.id), "trainer_id": str(trainer.id)}


@router.get("/stats")
def platform_stats(current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    total_users = db.query(func.count(User.id)).scalar()
    total_trainees = db.query(func.count(User.id)).filter(User.role == UserRole.trainee).scalar()
    total_trainers = db.query(func.count(User.id)).filter(User.role == UserRole.trainer).scalar()
    pending_approvals = db.query(func.count(User.id)).filter(User.is_approved.is_(False)).scalar()
    total_courses = db.query(func.count(Course.id)).scalar()
    published_courses = db.query(func.count(Course.id)).filter(Course.status == "published").scalar()
    total_enrollments = db.query(func.count(Enrollment.id)).scalar()
    avg_score = db.query(func.avg(AssessmentSubmission.score)).scalar()

    return {
        "total_users": total_users,
        "total_trainees": total_trainees,
        "total_trainers": total_trainers,
        "pending_approvals": pending_approvals,
        "total_courses": total_courses,
        "published_courses": published_courses,
        "total_enrollments": total_enrollments,
        "average_assessment_score": round(float(avg_score), 2) if avg_score is not None else None,
    }
