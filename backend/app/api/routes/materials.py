import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.course import Course, CourseMaterial, Enrollment
from app.models.user import User, UserRole
from app.schemas.course import CourseMaterialCreate, CourseMaterialOut
from app.api.deps import get_current_user, require_trainer

router = APIRouter(prefix="/api/courses/{course_id}/materials", tags=["materials"])


def _get_owned_course(db: Session, course_id: uuid.UUID, trainer: User) -> Course:
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if course.trainer_id != trainer.id:
        raise HTTPException(status_code=403, detail="Not your course")
    return course


@router.get("", response_model=list[CourseMaterialOut])
def list_materials(
    course_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    if current_user.role == UserRole.trainee:
        enrolled = (
            db.query(Enrollment)
            .filter(Enrollment.course_id == course_id, Enrollment.trainee_id == current_user.id)
            .first()
        )
        if not enrolled:
            raise HTTPException(status_code=403, detail="Enroll in this course to view materials")

    return db.query(CourseMaterial).filter(CourseMaterial.course_id == course_id).all()


@router.post("", response_model=CourseMaterialOut, status_code=status.HTTP_201_CREATED)
def upload_material(
    course_id: uuid.UUID,
    payload: CourseMaterialCreate,
    current_user: User = Depends(require_trainer),
    db: Session = Depends(get_db),
):
    """Registers a material's URL (e.g. from Supabase Storage / S3) against a course.

    File bytes are uploaded client-side directly to storage; this endpoint just
    records the resulting URL/title. See frontend UploadMaterial.jsx.
    """
    _get_owned_course(db, course_id, current_user)

    material = CourseMaterial(
        course_id=course_id,
        title=payload.title,
        file_url=payload.file_url,
        uploaded_by=current_user.id,
    )
    db.add(material)
    db.commit()
    db.refresh(material)
    return material


@router.delete("/{material_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_material(
    course_id: uuid.UUID,
    material_id: uuid.UUID,
    current_user: User = Depends(require_trainer),
    db: Session = Depends(get_db),
):
    _get_owned_course(db, course_id, current_user)
    material = (
        db.query(CourseMaterial)
        .filter(CourseMaterial.id == material_id, CourseMaterial.course_id == course_id)
        .first()
    )
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    db.delete(material)
    db.commit()
