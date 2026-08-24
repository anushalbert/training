"""Competency mapping logic: matches trainers to courses based on declared
trainer competencies vs. a course's required competencies.

Scoring: for every required competency the course lists, if a trainer has
that competency, they earn credit proportional to how their proficiency
compares to the required level (capped at 1.0 per competency, with partial
credit if under-qualified). Trainers with zero overlap are excluded.
"""

import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.course import Course, CourseCompetency
from app.models.user import User, TrainerCompetency, UserRole


@dataclass
class TrainerMatch:
    trainer: User
    match_score: float
    matched_competencies: list[str]


def suggest_trainers_for_course(db: Session, course_id: uuid.UUID, limit: int = 5) -> list[TrainerMatch]:
    course = db.query(Course).filter(Course.id == course_id).first()
    if course is None:
        return []

    required: list[CourseCompetency] = course.required_competencies
    if not required:
        return []

    trainers = (
        db.query(User)
        .filter(User.role == UserRole.trainer, User.is_approved.is_(True), User.is_active.is_(True))
        .all()
    )

    results: list[TrainerMatch] = []

    for trainer in trainers:
        trainer_skills = {tc.competency.lower(): tc.proficiency_level for tc in trainer.competencies}
        if not trainer_skills:
            continue

        matched: list[str] = []
        total_score = 0.0

        for req in required:
            key = req.competency.lower()
            if key in trainer_skills:
                proficiency = trainer_skills[key]
                # full credit if trainer meets/exceeds required level, else partial credit
                credit = min(1.0, proficiency / req.required_level) if req.required_level else 1.0
                total_score += credit
                matched.append(req.competency)

        if not matched:
            continue

        normalized_score = round(total_score / len(required), 4)
        results.append(TrainerMatch(trainer=trainer, match_score=normalized_score, matched_competencies=matched))

    results.sort(key=lambda m: m.match_score, reverse=True)
    return results[:limit]
