import uuid
from datetime import datetime, timezone

import anthropic
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.progress import TutorConversation
from app.models.user import User
from app.schemas.tutor import TutorMessageIn, TutorChatOut, TutorConversationOut
from app.api.deps import get_current_user
from app.api.routes.progress import _course_for_lesson, _require_enrolled
from app.services.tutor import build_system_prompt, get_tutor_reply

router = APIRouter(prefix="/api/lessons", tags=["tutor"])


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@router.get("/{lesson_id}/tutor/messages", response_model=TutorConversationOut)
def get_tutor_conversation(lesson_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    lesson, week, course = _course_for_lesson(db, lesson_id)
    _require_enrolled(db, course.id, current_user)

    convo = (
        db.query(TutorConversation)
        .filter(TutorConversation.user_id == current_user.id, TutorConversation.lesson_id == lesson_id)
        .first()
    )
    if not convo:
        return TutorConversationOut(lesson_id=lesson_id, messages=[], updated_at=None)
    return TutorConversationOut(lesson_id=lesson_id, messages=convo.messages, updated_at=convo.updated_at)


@router.post("/{lesson_id}/tutor/chat", response_model=TutorChatOut, status_code=status.HTTP_201_CREATED)
def chat_with_tutor(
    lesson_id: uuid.UUID,
    payload: TutorMessageIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lesson, week, course = _course_for_lesson(db, lesson_id)
    _require_enrolled(db, course.id, current_user)

    convo = (
        db.query(TutorConversation)
        .filter(TutorConversation.user_id == current_user.id, TutorConversation.lesson_id == lesson_id)
        .first()
    )
    if not convo:
        convo = TutorConversation(user_id=current_user.id, lesson_id=lesson_id, messages=[])
        db.add(convo)
        db.flush()

    history = list(convo.messages) + [{"role": "user", "content": payload.message, "timestamp": _now_iso()}]

    system_prompt = build_system_prompt(course, week, lesson, course.weeks)

    try:
        reply_text = get_tutor_reply(system_prompt, history)
    except RuntimeError:
        raise HTTPException(status_code=503, detail="AI tutor is not configured yet")
    except anthropic.RateLimitError:
        raise HTTPException(status_code=429, detail="Tutor is busy, try again shortly")
    except anthropic.APIStatusError as e:
        raise HTTPException(status_code=502, detail=f"Tutor request failed: {e.message}")
    except anthropic.APIConnectionError:
        raise HTTPException(status_code=502, detail="Could not reach the tutor service")

    history.append({"role": "assistant", "content": reply_text, "timestamp": _now_iso()})
    convo.messages = history
    db.commit()
    db.refresh(convo)

    return TutorChatOut(lesson_id=lesson_id, messages=convo.messages)
