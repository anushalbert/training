import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.assessment import Assessment, AssessmentQuestion, AssessmentSubmission, QuestionType
from app.models.course import Course, Enrollment
from app.models.user import User, UserRole
from app.schemas.assessment import (
    AssessmentCreate,
    AssessmentDetail,
    AssessmentOut,
    QuestionOut,
    QuestionOutWithAnswer,
    SubmissionCreate,
    SubmissionOut,
)
from app.api.deps import get_current_user, require_trainer

router = APIRouter(prefix="/api/assessments", tags=["assessments"])


@router.post("", response_model=AssessmentDetail, status_code=status.HTTP_201_CREATED)
def create_assessment(
    payload: AssessmentCreate,
    current_user: User = Depends(require_trainer),
    db: Session = Depends(get_db),
):
    course = db.query(Course).filter(Course.id == payload.course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if course.trainer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your course")

    assessment = Assessment(course_id=payload.course_id, title=payload.title, created_by=current_user.id)
    db.add(assessment)
    db.flush()

    for q in payload.questions:
        db.add(AssessmentQuestion(assessment_id=assessment.id, **q.model_dump()))

    db.commit()
    db.refresh(assessment)
    return _to_detail_with_answers(assessment)


@router.get("/course/{course_id}", response_model=list[AssessmentOut])
def list_assessments_for_course(
    course_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.query(Assessment).filter(Assessment.course_id == course_id).all()


@router.get("/{assessment_id}", response_model=AssessmentDetail)
def get_assessment(
    assessment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    # Trainees taking the test never receive the correct answer in the payload.
    if current_user.role == UserRole.trainee:
        questions = [QuestionOut.model_validate(q) for q in assessment.questions]
        return AssessmentDetail(
            id=assessment.id,
            course_id=assessment.course_id,
            title=assessment.title,
            created_by=assessment.created_by,
            created_at=assessment.created_at,
            questions=questions,
        )

    return _to_detail_with_answers(assessment)


def _to_detail_with_answers(assessment: Assessment) -> AssessmentDetail:
    questions = [QuestionOutWithAnswer.model_validate(q) for q in assessment.questions]
    return AssessmentDetail(
        id=assessment.id,
        course_id=assessment.course_id,
        title=assessment.title,
        created_by=assessment.created_by,
        created_at=assessment.created_at,
        questions=questions,
    )


@router.post("/{assessment_id}/submit", response_model=SubmissionOut, status_code=status.HTTP_201_CREATED)
def submit_assessment(
    assessment_id: uuid.UUID,
    payload: SubmissionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != UserRole.trainee:
        raise HTTPException(status_code=403, detail="Only trainees can submit assessments")

    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    enrolled = (
        db.query(Enrollment)
        .filter(Enrollment.course_id == assessment.course_id, Enrollment.trainee_id == current_user.id)
        .first()
    )
    if not enrolled:
        raise HTTPException(status_code=403, detail="Enroll in this course to take the assessment")

    existing = (
        db.query(AssessmentSubmission)
        .filter(
            AssessmentSubmission.assessment_id == assessment_id,
            AssessmentSubmission.trainee_id == current_user.id,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Assessment already submitted")

    questions = assessment.questions
    total = len(questions)
    correct = 0
    for q in questions:
        submitted_answer = payload.answers.get(q.id)
        if not submitted_answer:
            continue
        if q.question_type in (QuestionType.mcq, QuestionType.true_false):
            is_correct = submitted_answer.strip().upper() == q.correct_answer.strip().upper()
        else:
            # fill_in_blank / short_answer: best-effort normalized text match
            is_correct = submitted_answer.strip().lower() == q.correct_answer.strip().lower()
        if is_correct:
            correct += 1

    score = round((correct / total) * 100, 2) if total else 0.0

    submission = AssessmentSubmission(
        assessment_id=assessment_id,
        trainee_id=current_user.id,
        score=score,
        total_questions=total,
        answers={str(k): v for k, v in payload.answers.items()},
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission


@router.get("/{assessment_id}/submissions", response_model=list[SubmissionOut])
def list_submissions(
    assessment_id: uuid.UUID,
    current_user: User = Depends(require_trainer),
    db: Session = Depends(get_db),
):
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    if assessment.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not your assessment")
    return db.query(AssessmentSubmission).filter(AssessmentSubmission.assessment_id == assessment_id).all()
