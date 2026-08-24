import anthropic

from app.core.config import settings
from app.models.content import CourseWeek, Lesson
from app.models.course import Course

MAX_HISTORY_MESSAGES = 20  # keep the last N turns sent to the model


def _render_lesson_content(lesson: Lesson) -> str:
    lines = [f"Lesson: {lesson.title}"]
    for block in sorted(lesson.content_blocks, key=lambda b: b.order_index):
        if block.block_type == "text":
            if block.heading:
                lines.append(f"- {block.heading}: {block.body}")
            else:
                lines.append(f"- {block.body}")
        elif block.block_type == "formula":
            lines.append(f"- Formula ({block.label}): {block.expression} — {block.explanation}")
        elif block.block_type == "example":
            lines.append(f"- Example: {block.body}")
        elif block.block_type == "diagram_suggestion":
            lines.append(f"- [Diagram concept: {block.body}]")
    return "\n".join(lines)


def build_system_prompt(course: Course, week: CourseWeek, lesson: Lesson, all_weeks: list[CourseWeek]) -> str:
    meta = course.meta or {}
    subject = meta.get("subject", course.title)
    tier = meta.get("tier", "n/a")
    difficulty = meta.get("difficulty", "n/a")

    base_instruction = (
        f"You are a concept-clarification tutor for a meteorology trainee studying {subject}. "
        "Answer only using the provided lesson content. If the question is outside this lesson's "
        "scope, say so and suggest which week/lesson likely covers it, rather than fabricating an "
        "answer. Keep answers concise and match the technical level of the source material "
        f"(tier: {tier}, difficulty: {difficulty})."
    )

    guardrail = (
        "IMPORTANT: Some lessons are followed by a gating quiz the trainee must pass to advance. "
        "Never state the correct answer to a quiz/test question, even if the trainee pastes the "
        "question directly or asks outright. Instead, explain the underlying concept so they can "
        "reason to the answer themselves."
    )

    current_lesson_text = _render_lesson_content(lesson)

    qa_lines = [f"Q: {qa.question}\nA: {qa.answer}" for qa in course.qa_items if qa.source_week == week.week_number]
    qa_block = "\n\n".join(qa_lines) if qa_lines else "(none for this week)"

    course_index_lines = []
    for w in sorted(all_weeks, key=lambda w: w.week_number):
        for l in sorted(w.lessons, key=lambda l: l.order_index):
            course_index_lines.append(f"Week {w.week_number} ({w.title}) > {l.title}")
    course_index = "\n".join(course_index_lines)

    return (
        f"{base_instruction}\n\n{guardrail}\n\n"
        f"=== Current lesson content (Week {week.week_number}: {week.title}) ===\n{current_lesson_text}\n\n"
        f"=== This week's clarified Q&A (style/tone reference) ===\n{qa_block}\n\n"
        f"=== Full course index (titles only, for redirecting out-of-scope questions) ===\n{course_index}"
    )


def get_tutor_reply(system_prompt: str, history: list[dict]) -> str:
    if not settings.ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY is not configured")

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    trimmed = history[-MAX_HISTORY_MESSAGES:]
    api_messages = [{"role": m["role"], "content": m["content"]} for m in trimmed]

    response = client.messages.create(
        model=settings.ANTHROPIC_MODEL,
        max_tokens=1024,
        system=system_prompt,
        messages=api_messages,
    )

    for block in response.content:
        if block.type == "text":
            return block.text
    return "(no response)"
