import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.course import Course, Enrollment
from app.models.assessment import Assessment, AssessmentQuestion, QuestionType
from app.models.content import CourseWeek, Lesson, LessonContentBlock, LessonNoteAnchor, WeekCompletionCriterion, CourseQAItem
from app.models.user import User, UserRole
from app.schemas.content import CourseContentImport, ImportResult, WeekOut, QAItemOut
from app.api.deps import get_current_user, require_trainer_or_admin

router = APIRouter(prefix="/api/courses", tags=["content"])


def _get_course_for_write(db: Session, course_id: uuid.UUID, current_user: User) -> Course:
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if current_user.role == UserRole.trainer and course.trainer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your course")
    return course


def _get_course_for_read(db: Session, course_id: uuid.UUID, current_user: User) -> Course:
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
            raise HTTPException(status_code=403, detail="Enroll in this course to view its content")
    elif current_user.role == UserRole.trainer and course.trainer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your course")
    return course


def _map_correct_answer_to_letter(options: list[str], correct_answer: str) -> str | None:
    normalized_target = correct_answer.strip().lower()
    for i, opt in enumerate(options):
        if opt is not None and opt.strip().lower() == normalized_target:
            return "ABCD"[i]
    return None


@router.post("/{course_id}/import-content", response_model=ImportResult, status_code=status.HTTP_201_CREATED)
def import_course_content(
    course_id: uuid.UUID,
    payload: CourseContentImport,
    current_user: User = Depends(require_trainer_or_admin),
    db: Session = Depends(get_db),
):
    course = _get_course_for_write(db, course_id, current_user)

    course.meta = {
        **(course.meta or {}),
        "subject": payload.course_meta.subject,
        "source_pdf": payload.course_meta.source_pdf,
        "source_url": payload.course_meta.source_url,
        "author": payload.course_meta.author,
        "tier": payload.course_meta.tier,
        "difficulty": payload.course_meta.difficulty,
        "total_weeks": payload.course_meta.total_weeks,
        "estimated_hours": payload.course_meta.estimated_hours,
        "prerequisites": payload.course_meta.prerequisites,
    }

    weeks_created = 0
    lessons_created = 0

    try:
        for week_in in payload.weeks:
            week = CourseWeek(
                course_id=course.id,
                week_number=week_in.week_number,
                title=week_in.title,
                overview=week_in.overview,
                estimated_minutes=week_in.estimated_minutes,
            )
            db.add(week)
            db.flush()
            weeks_created += 1

            for ci, criterion_text in enumerate(week_in.completion_criteria):
                db.add(WeekCompletionCriterion(week_id=week.id, criterion_text=criterion_text, order_index=ci))

            for li, lesson_in in enumerate(week_in.lessons):
                lesson = Lesson(week_id=week.id, lesson_key=lesson_in.lesson_id, title=lesson_in.title, order_index=li)
                db.add(lesson)
                db.flush()
                lessons_created += 1

                for bi, block_in in enumerate(lesson_in.content_blocks):
                    db.add(
                        LessonContentBlock(
                            lesson_id=lesson.id,
                            order_index=bi,
                            block_type=block_in.type,
                            heading=block_in.heading,
                            body=block_in.body,
                            label=block_in.label,
                            expression=block_in.expression,
                            explanation=block_in.explanation,
                        )
                    )

                for anchor_in in lesson_in.note_anchors:
                    db.add(
                        LessonNoteAnchor(
                            lesson_id=lesson.id,
                            anchor_text=anchor_in.anchor_text,
                            suggested_note_prompt=anchor_in.suggested_note_prompt,
                        )
                    )

        qa_items_created = 0
        for qa_in in payload.ai_qa_concept_clarification:
            db.add(
                CourseQAItem(
                    course_id=course.id,
                    question=qa_in.question,
                    answer=qa_in.answer,
                    source_week=qa_in.source_week,
                    difficulty=qa_in.difficulty,
                )
            )
            qa_items_created += 1

        assessment_id = None
        questions_created = 0
        skipped_questions: list[str] = []

        if payload.create_assessment and payload.ai_test_questions:
            assessment = Assessment(
                course_id=course.id,
                title=f"{payload.course_meta.subject} Knowledge Check",
                created_by=current_user.id,
            )
            db.add(assessment)
            db.flush()
            assessment_id = assessment.id

            for q_in in payload.ai_test_questions:
                q_type = QuestionType(q_in.type)

                if q_type in (QuestionType.mcq, QuestionType.true_false):
                    options = (q_in.options or [])[:4]
                    letter = _map_correct_answer_to_letter(options, q_in.correct_answer)
                    if letter is None:
                        skipped_questions.append(q_in.question)
                        continue
                    padded = options + [None] * (4 - len(options))
                    db.add(
                        AssessmentQuestion(
                            assessment_id=assessment.id,
                            question_type=q_type,
                            question_text=q_in.question,
                            option_a=padded[0],
                            option_b=padded[1],
                            option_c=padded[2],
                            option_d=padded[3],
                            correct_answer=letter,
                            competency_tag=None,
                            source_week=q_in.source_week,
                        )
                    )
                else:
                    db.add(
                        AssessmentQuestion(
                            assessment_id=assessment.id,
                            question_type=q_type,
                            question_text=q_in.question,
                            correct_answer=q_in.correct_answer,
                            competency_tag=None,
                            source_week=q_in.source_week,
                        )
                    )
                questions_created += 1

        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Content already imported for this course (duplicate week numbers). Use a different course, or this is a re-import.",
        )

    return ImportResult(
        course_id=course.id,
        weeks_created=weeks_created,
        lessons_created=lessons_created,
        qa_items_created=qa_items_created,
        assessment_id=assessment_id,
        questions_created=questions_created,
        skipped_questions=skipped_questions,
    )


@router.get("/{course_id}/weeks", response_model=list[WeekOut])
def get_course_weeks(course_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    course = _get_course_for_read(db, course_id, current_user)
    return course.weeks


@router.get("/{course_id}/qa", response_model=list[QAItemOut])
def get_course_qa(course_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    course = _get_course_for_read(db, course_id, current_user)
    return course.qa_items
