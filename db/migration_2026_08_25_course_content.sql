-- Migration applied to the live Supabase DB on 2026-08-25.
-- Brings an already-deployed database up to the schema.sql shape that adds
-- structured course content (weeks/lessons/content blocks) and generalized
-- (mcq/true_false/fill_in_blank/short_answer) assessment questions.
-- Safe to run on a DB with no course/assessment data yet.

ALTER TABLE courses ADD COLUMN IF NOT EXISTS meta JSONB NOT NULL DEFAULT '{}'::jsonb;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'question_type') THEN
        CREATE TYPE question_type AS ENUM ('mcq', 'true_false', 'fill_in_blank', 'short_answer');
    END IF;
END $$;

DROP TABLE IF EXISTS assessment_questions CASCADE;

CREATE TABLE assessment_questions (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id     UUID NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
    question_type     question_type NOT NULL DEFAULT 'mcq',
    question_text     TEXT NOT NULL,
    option_a          VARCHAR(500),
    option_b          VARCHAR(500),
    option_c          VARCHAR(500),
    option_d          VARCHAR(500),
    correct_answer    VARCHAR(500) NOT NULL,
    competency_tag    VARCHAR(120)
);

CREATE INDEX idx_questions_assessment ON assessment_questions(assessment_id);

CREATE TABLE IF NOT EXISTS course_weeks (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id          UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    week_number        INTEGER NOT NULL,
    title              VARCHAR(200) NOT NULL,
    overview           TEXT,
    estimated_minutes  INTEGER,
    UNIQUE (course_id, week_number)
);

CREATE INDEX IF NOT EXISTS idx_weeks_course ON course_weeks(course_id);

CREATE TABLE IF NOT EXISTS lessons (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    week_id            UUID NOT NULL REFERENCES course_weeks(id) ON DELETE CASCADE,
    lesson_key         VARCHAR(50),
    title              VARCHAR(200) NOT NULL,
    order_index        INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_lessons_week ON lessons(week_id);

CREATE TABLE IF NOT EXISTS lesson_content_blocks (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lesson_id          UUID NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
    order_index        INTEGER NOT NULL DEFAULT 0,
    block_type         VARCHAR(20) NOT NULL CHECK (block_type IN ('text', 'formula', 'example')),
    heading            VARCHAR(200),
    body               TEXT,
    label              VARCHAR(200),
    expression         TEXT,
    explanation        TEXT
);

CREATE INDEX IF NOT EXISTS idx_content_blocks_lesson ON lesson_content_blocks(lesson_id);

CREATE TABLE IF NOT EXISTS lesson_note_anchors (
    id                     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lesson_id              UUID NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
    anchor_text            TEXT,
    suggested_note_prompt  TEXT
);

CREATE INDEX IF NOT EXISTS idx_note_anchors_lesson ON lesson_note_anchors(lesson_id);

CREATE TABLE IF NOT EXISTS week_completion_criteria (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    week_id            UUID NOT NULL REFERENCES course_weeks(id) ON DELETE CASCADE,
    criterion_text     TEXT NOT NULL,
    order_index        INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_completion_criteria_week ON week_completion_criteria(week_id);

CREATE TABLE IF NOT EXISTS course_qa_items (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id          UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    question           TEXT NOT NULL,
    answer             TEXT NOT NULL,
    source_week        INTEGER,
    difficulty         VARCHAR(20)
);

CREATE INDEX IF NOT EXISTS idx_qa_items_course ON course_qa_items(course_id);
