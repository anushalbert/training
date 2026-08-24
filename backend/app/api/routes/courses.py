import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.course import Course, CourseCompetency, Enrollment
from app.models.user import User, UserRole
from app.schemas.course import CourseCreate, CourseOut, CourseUpdate, EnrollmentOut
from app.api.deps import get_current_user, require_trainer, require_trainer_or_admin

router = APIRouter(prefix="/api/courses", tags=["courses"])


@router.get("", response_model=list[CourseOut])
def list_courses(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = db.query(Course)
    if current_user.role == UserRole.trainee:
        query = query.filter(Course.status == "published")
    elif current_user.role == UserRole.trainer:
        query = query.filter(Course.trainer_id == current_user.id)
    return query.order_by(Course.created_at.desc()).all()


@router.post("", response_model=CourseOut, status_code=status.HTTP_201_CREATED)
def create_course(
    payload: CourseCreate,
    current_user: User = Depends(require_trainer_or_admin),
    db: Session = Depends(get_db),
):
    course = Course(
        title=payload.title,
        description=payload.description,
        trainer_id=current_user.id if current_user.role == UserRole.trainer else None,
    )
    db.add(course)
    db.flush()

    for req in payload.required_competencies:
        db.add(CourseCompetency(course_id=course.id, competency=req.competency, required_level=req.required_level))

    db.commit()
    db.refresh(course)
    return course


@router.get("/{course_id}", response_model=CourseOut)
def get_course(course_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


@router.patch("/{course_id}", response_model=CourseOut)
def update_course(
    course_id: uuid.UUID,
    payload: CourseUpdate,
    current_user: User = Depends(require_trainer_or_admin),
    db: Session = Depends(get_db),
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if current_user.role == UserRole.trainer and course.trainer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your course")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(course, field, value)

    db.commit()
    db.refresh(course)
    return course


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(
    course_id: uuid.UUID,
    current_user: User = Depends(require_trainer_or_admin),
    db: Session = Depends(get_db),
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if current_user.role == UserRole.trainer and course.trainer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your course")
    db.delete(course)
    db.commit()


@router.post("/{course_id}/enroll", response_model=EnrollmentOut, status_code=status.HTTP_201_CREATED)
def enroll_in_course(
    course_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != UserRole.trainee:
        raise HTTPException(status_code=403, detail="Only trainees can enroll")

    course = db.query(Course).filter(Course.id == course_id, Course.status == "published").first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found or not published")

    existing = (
        db.query(Enrollment)
        .filter(Enrollment.course_id == course_id, Enrollment.trainee_id == current_user.id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Already enrolled")

    enrollment = Enrollment(course_id=course_id, trainee_id=current_user.id)
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    return enrollment


@router.get("/me/enrollments", response_model=list[EnrollmentOut])
def my_enrollments(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Enrollment).filter(Enrollment.trainee_id == current_user.id).all()
