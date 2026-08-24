-- Migration applied to the live Supabase DB on 2026-08-25.
-- Adds per-week gated quizzes, lesson progress tracking, notes, and a table
-- for future AI tutor conversation logging.

ALTER TABLE assessment_questions ADD COLUMN IF NOT EXISTS source_week INTEGER;
CREATE INDEX IF NOT EXISTS idx_questions_source_week ON assessment_questions(assessment_id, source_week);

ALTER TABLE lesson_content_blocks DROP CONSTRAINT IF EXISTS ck_block_type;
ALTER TABLE lesson_content_blocks ADD CONSTRAINT ck_block_type
    CHECK (block_type IN ('text', 'formula', 'example', 'diagram_suggestion'));

CREATE TABLE IF NOT EXISTS user_progress (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id            UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id          UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    week_number        INTEGER NOT NULL,
    lesson_id          UUID NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
    completed_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, lesson_id)
);

CREATE INDEX IF NOT EXISTS idx_progress_user_course ON user_progress(user_id, course_id);

CREATE TABLE IF NOT EXISTS quiz_attempts (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id            UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    week_id            UUID NOT NULL REFERENCES course_weeks(id) ON DELETE CASCADE,
    score              NUMERIC(5,2) NOT NULL DEFAULT 0,
    passed             BOOLEAN NOT NULL DEFAULT FALSE,
    answers            JSONB NOT NULL DEFAULT '{}'::jsonb,
    attempted_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_quiz_attempts_user_week ON quiz_attempts(user_id, week_id);

CREATE TABLE IF NOT EXISTS notes (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id            UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    lesson_id          UUID NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
    anchor_text        TEXT,
    note_text          TEXT NOT NULL,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_notes_user_lesson ON notes(user_id, lesson_id);

CREATE TABLE IF NOT EXISTS tutor_conversations (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id            UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    lesson_id          UUID NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
    messages           JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_tutor_conversations_user_lesson ON tutor_conversations(user_id, lesson_id);
