from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User, TrainerCompetency, UserRole
from app.schemas.user import UserOut, UserProfileUpdate, TrainerCompetencyIn, TrainerCompetencyOut
from app.api.deps import get_current_user, require_trainer

router = APIRouter(prefix="/api/users", tags=["users"])


@router.patch("/me", response_model=UserOut)
def update_my_profile(
    payload: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.full_name is not None:
        current_user.full_name = payload.full_name
    if payload.bio is not None:
        current_user.bio = payload.bio
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/me/competencies", response_model=list[TrainerCompetencyOut])
def list_my_competencies(
    current_user: User = Depends(require_trainer),
    db: Session = Depends(get_db),
):
    return db.query(TrainerCompetency).filter(TrainerCompetency.trainer_id == current_user.id).all()


@router.put("/me/competencies", response_model=list[TrainerCompetencyOut])
def set_my_competencies(
    payload: list[TrainerCompetencyIn],
    current_user: User = Depends(require_trainer),
    db: Session = Depends(get_db),
):
    """Replaces the trainer's full competency list with the given set."""
    db.query(TrainerCompetency).filter(TrainerCompetency.trainer_id == current_user.id).delete()
    rows = [
        TrainerCompetency(
            trainer_id=current_user.id,
            competency=item.competency,
            proficiency_level=item.proficiency_level,
        )
        for item in payload
    ]
    db.add_all(rows)
    db.commit()
    return db.query(TrainerCompetency).filter(TrainerCompetency.trainer_id == current_user.id).all()


@router.get("/trainers", response_model=list[UserOut])
def list_trainers(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return (
        db.query(User)
        .filter(User.role == UserRole.trainer, User.is_approved.is_(True), User.is_active.is_(True))
        .all()
    )
