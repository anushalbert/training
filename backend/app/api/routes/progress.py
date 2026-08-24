import random
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.assessment import Assessment, AssessmentQuestion, QuestionType
from app.models.content import CourseWeek, Lesson
from app.models.course import Course, Enrollment
from app.models.progress import UserProgress, QuizAttempt, Note
from app.models.user import User, UserRole
from app.schemas.progress import (
    LessonCompleteOut,
    CourseProgress,
    WeekProgress,
    WeekQuizOut,
    QuizQuestionOut,
    QuizSubmitIn,
    QuizResultOut,
    NoteCreate,
    NoteOut,
)
from app.api.deps import get_current_user

router = APIRouter(prefix="/api", tags=["progress"])

PASSING_THRESHOLD = 70.0


def _require_enrolled(db: Session, course_id: uuid.UUID, user: User) -> Course:
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if user.role != UserRole.trainee:
        raise HTTPException(status_code=403, detail="Only trainees have course progress")
    enrolled = (
        db.query(Enrollment).filter(Enrollment.course_id == course_id, Enrollment.trainee_id == user.id).first()
    )
    if not enrolled:
        raise HTTPException(status_code=403, detail="Enroll in this course first")
    return course


def _course_for_lesson(db: Session, lesson_id: uuid.UUID) -> tuple[Lesson, CourseWeek, Course]:
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    week = lesson.week
    course = week.course
    return lesson, week, course


def _compute_week_progress_list(db: Session, user: User, course: Course) -> list[WeekProgress]:
    weeks = db.query(CourseWeek).filter(CourseWeek.course_id == course.id).order_by(CourseWeek.week_number).all()
    all_lesson_ids = [lesson.id for week in weeks for lesson in week.lessons]

    completed_ids = set()
    if all_lesson_ids:
        rows = (
            db.query(UserProgress)
            .filter(UserProgress.user_id == user.id, UserProgress.lesson_id.in_(all_lesson_ids))
            .all()
        )
        completed_ids = {r.lesson_id for r in rows}

    result: list[WeekProgress] = []
    prev_passed = True  # week 1 is always unlocked

    for week in weeks:
        lesson_ids = [lesson.id for lesson in week.lessons]
        total = len(lesson_ids)
        completed = len([lid for lid in lesson_ids if lid in completed_ids])
        lessons_done = total > 0 and completed == total

        q_count = (
            db.query(AssessmentQuestion)
            .join(Assessment, Assessment.id == AssessmentQuestion.assessment_id)
            .filter(Assessment.course_id == course.id, AssessmentQuestion.source_week == week.week_number)
            .count()
        )
        quiz_required = q_count > 0

        attempts = db.query(QuizAttempt).filter(QuizAttempt.user_id == user.id, QuizAttempt.week_id == week.id).all()
        quiz_passed = any(a.passed for a in attempts)
        best_score = max((float(a.score) for a in attempts), default=None)

        unlocked = prev_passed
        week_passed_overall = lessons_done and (quiz_passed if quiz_required else True)

        result.append(
            WeekProgress(
                week_number=week.week_number,
                week_id=week.id,
                total_lessons=total,
                completed_lessons=completed,
                lessons_done=lessons_done,
                quiz_required=quiz_required,
                quiz_passed=quiz_passed,
                unlocked=unlocked,
                best_score=best_score,
                attempts=len(attempts),
            )
        )
        prev_passed = week_passed_overall

    return result


@router.get("/courses/{course_id}/progress", response_model=CourseProgress)
def get_course_progress(course_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    course = _require_enrolled(db, course_id, current_user)
    week_list = _compute_week_progress_list(db, current_user, course)

    total_lessons = sum(w.total_lessons for w in week_list)
    completed_lessons = sum(w.completed_lessons for w in week_list)
    percent = round(completed_lessons / total_lessons * 100, 1) if total_lessons else 0.0

    weeks = db.query(CourseWeek).filter(CourseWeek.course_id == course_id).order_by(CourseWeek.week_number).all()
    all_lesson_ids = [lesson.id for week in weeks for lesson in week.lessons]
    completed_ids = []
    if all_lesson_ids:
        rows = (
            db.query(UserProgress)
            .filter(UserProgress.user_id == current_user.id, UserProgress.lesson_id.in_(all_lesson_ids))
            .all()
        )
        completed_ids = [r.lesson_id for r in rows]

    return CourseProgress(
        course_id=course.id,
        total_lessons=total_lessons,
        completed_lessons=completed_lessons,
        percent=percent,
        completed_lesson_ids=completed_ids,
        weeks=week_list,
    )


@router.post("/lessons/{lesson_id}/complete", response_model=LessonCompleteOut, status_code=status.HTTP_201_CREATED)
def complete_lesson(lesson_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    lesson, week, course = _course_for_lesson(db, lesson_id)
    _require_enrolled(db, course.id, current_user)

    week_list = _compute_week_progress_list(db, current_user, course)
    this_week = next((w for w in week_list if w.week_number == week.week_number), None)
    if this_week is None or not this_week.unlocked:
        raise HTTPException(status_code=403, detail="This week is locked")

    existing = (
        db.query(UserProgress)
        .filter(UserProgress.user_id == current_user.id, UserProgress.lesson_id == lesson_id)
        .first()
    )
    if existing:
        return LessonCompleteOut(lesson_id=lesson_id, completed_at=existing.completed_at)

    row = UserProgress(user_id=current_user.id, course_id=course.id, week_number=week.week_number, lesson_id=lesson_id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return LessonCompleteOut(lesson_id=lesson_id, completed_at=row.completed_at)


@router.get("/courses/{course_id}/weeks/{week_number}/quiz", response_model=WeekQuizOut)
def get_week_quiz(
    course_id: uuid.UUID,
    week_number: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    course = _require_enrolled(db, course_id, current_user)
    week = db.query(CourseWeek).filter(CourseWeek.course_id == course_id, CourseWeek.week_number == week_number).first()
    if not week:
        raise HTTPException(status_code=404, detail="Week not found")

    week_list = _compute_week_progress_list(db, current_user, course)
    this_week = next((w for w in week_list if w.week_number == week_number), None)
    if this_week is None or not this_week.unlocked:
        raise HTTPException(status_code=403, detail="This week is locked")
    if not this_week.lessons_done:
        raise HTTPException(status_code=403, detail="Complete all lessons in this week before taking the quiz")

    questions = (
        db.query(AssessmentQuestion)
        .join(Assessment, Assessment.id == AssessmentQuestion.assessment_id)
        .filter(Assessment.course_id == course_id, AssessmentQuestion.source_week == week_number)
        .all()
    )
    if not questions:
        raise HTTPException(status_code=404, detail="No quiz configured for this week")

    shuffled = questions[:]
    random.shuffle(shuffled)

    return WeekQuizOut(
        week_id=week.id,
        week_number=week_number,
        questions=[QuizQuestionOut.model_validate(q) for q in shuffled],
        passing_threshold=PASSING_THRESHOLD,
    )


@router.post("/courses/{course_id}/weeks/{week_number}/quiz/submit", response_model=QuizResultOut, status_code=status.HTTP_201_CREATED)
def submit_week_quiz(
    course_id: uuid.UUID,
    week_number: int,
    payload: QuizSubmitIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    course = _require_enrolled(db, course_id, current_user)
    week = db.query(CourseWeek).filter(CourseWeek.course_id == course_id, CourseWeek.week_number == week_number).first()
    if not week:
        raise HTTPException(status_code=404, detail="Week not found")

    week_list = _compute_week_progress_list(db, current_user, course)
    this_week = next((w for w in week_list if w.week_number == week_number), None)
    if this_week is None or not this_week.unlocked:
        raise HTTPException(status_code=403, detail="This week is locked")
    if not this_week.lessons_done:
        raise HTTPException(status_code=403, detail="Complete all lessons in this week before taking the quiz")

    questions = (
        db.query(AssessmentQuestion)
        .join(Assessment, Assessment.id == AssessmentQuestion.assessment_id)
        .filter(Assessment.course_id == course_id, AssessmentQuestion.source_week == week_number)
        .all()
    )
    if not questions:
        raise HTTPException(status_code=404, detail="No quiz configured for this week")

    auto_gradable = [q for q in questions if q.question_type != QuestionType.short_answer]
    correct = 0
    short_flagged: list[uuid.UUID] = []

    for q in questions:
        submitted = payload.answers.get(q.id)
        if q.question_type == QuestionType.short_answer:
            short_flagged.append(q.id)
            continue
        if not submitted:
            continue
        if q.question_type in (QuestionType.mcq, QuestionType.true_false):
            is_correct = submitted.strip().upper() == q.correct_answer.strip().upper()
        else:
            is_correct = submitted.strip().lower() == q.correct_answer.strip().lower()
        if is_correct:
            correct += 1

    total_auto = len(auto_gradable)
    score = round((correct / total_auto) * 100, 2) if total_auto else 100.0
    passed = score >= PASSING_THRESHOLD

    attempt = QuizAttempt(
        user_id=current_user.id,
        week_id=week.id,
        score=score,
        passed=passed,
        answers={str(k): v for k, v in payload.answers.items()},
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    return QuizResultOut(
        attempt_id=attempt.id,
        score=score,
        passed=passed,
        correct_count=correct,
        total_auto_gradable=total_auto,
        short_answer_flagged=short_flagged,
        next_week_unlocked=passed,
    )


@router.post("/lessons/{lesson_id}/notes", response_model=NoteOut, status_code=status.HTTP_201_CREATED)
def create_note(
    lesson_id: uuid.UUID,
    payload: NoteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lesson, week, course = _course_for_lesson(db, lesson_id)
    _require_enrolled(db, course.id, current_user)

    note = Note(user_id=current_user.id, lesson_id=lesson_id, anchor_text=payload.anchor_text, note_text=payload.note_text)
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


@router.get("/lessons/{lesson_id}/notes", response_model=list[NoteOut])
def list_notes(lesson_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    lesson, week, course = _course_for_lesson(db, lesson_id)
    _require_enrolled(db, course.id, current_user)
    return (
        db.query(Note)
        .filter(Note.lesson_id == lesson_id, Note.user_id == current_user.id)
        .order_by(Note.created_at.desc())
        .all()
    )


@router.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(note_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    if note.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your note")
    db.delete(note)
    db.commit()
