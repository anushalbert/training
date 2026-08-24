-- ============================================================================
-- Training Platform — PostgreSQL schema
-- Run this on a fresh database (local Postgres, Docker init, or Supabase SQL editor).
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto"; -- gen_random_uuid()

-- ---------------------------------------------------------------------------
-- ENUM types
-- ---------------------------------------------------------------------------
CREATE TYPE user_role AS ENUM ('trainee', 'trainer', 'admin');
CREATE TYPE course_status AS ENUM ('draft', 'published', 'archived');
CREATE TYPE enrollment_status AS ENUM ('enrolled', 'completed', 'dropped');

-- ---------------------------------------------------------------------------
-- users
-- ---------------------------------------------------------------------------
CREATE TABLE users (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name         VARCHAR(150) NOT NULL,
    email             VARCHAR(255) NOT NULL UNIQUE,
    hashed_password   VARCHAR(255) NOT NULL,
    role              user_role NOT NULL DEFAULT 'trainee',
    is_approved       BOOLEAN NOT NULL DEFAULT FALSE,
    is_active         BOOLEAN NOT NULL DEFAULT TRUE,
    bio               TEXT,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_email ON users(email);

-- ---------------------------------------------------------------------------
-- trainer_competencies — a trainer's declared skills + proficiency
-- ---------------------------------------------------------------------------
CREATE TABLE trainer_competencies (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trainer_id        UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    competency        VARCHAR(120) NOT NULL,
    proficiency_level SMALLINT NOT NULL CHECK (proficiency_level BETWEEN 1 AND 5),
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (trainer_id, competency)
);

-- ---------------------------------------------------------------------------
-- courses
-- ---------------------------------------------------------------------------
CREATE TABLE courses (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title             VARCHAR(200) NOT NULL,
    description       TEXT,
    trainer_id        UUID REFERENCES users(id) ON DELETE SET NULL,
    status            course_status NOT NULL DEFAULT 'draft',
    -- free-form course metadata: tier, difficulty, estimated_hours, prerequisites,
    -- source_pdf, source_url, author — set on import, rendered as-is by the frontend.
    meta              JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_courses_trainer ON courses(trainer_id);
CREATE INDEX idx_courses_status ON courses(status);

-- ---------------------------------------------------------------------------
-- course_competencies — competencies a course requires (used for matching)
-- ---------------------------------------------------------------------------
CREATE TABLE course_competencies (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id         UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    competency        VARCHAR(120) NOT NULL,
    required_level    SMALLINT NOT NULL DEFAULT 1 CHECK (required_level BETWEEN 1 AND 5),
    UNIQUE (course_id, competency)
);

-- ---------------------------------------------------------------------------
-- course_materials — files/links uploaded by trainers
-- ---------------------------------------------------------------------------
CREATE TABLE course_materials (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id         UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    title             VARCHAR(200) NOT NULL,
    file_url          TEXT NOT NULL,
    uploaded_by       UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_materials_course ON course_materials(course_id);

-- ---------------------------------------------------------------------------
-- enrollments
-- ---------------------------------------------------------------------------
CREATE TABLE enrollments (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id         UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    trainee_id        UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status            enrollment_status NOT NULL DEFAULT 'enrolled',
    enrolled_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (course_id, trainee_id)
);

CREATE INDEX idx_enrollments_trainee ON enrollments(trainee_id);
CREATE INDEX idx_enrollments_course ON enrollments(course_id);

-- ---------------------------------------------------------------------------
-- course_weeks / lessons / lesson_content_blocks / lesson_note_anchors /
-- week_completion_criteria / course_qa_items — structured lesson content,
-- populated via the bulk course-content import endpoint (see
-- POST /api/courses/{id}/import-content) rather than authored one row at a time.
-- ---------------------------------------------------------------------------
CREATE TABLE course_weeks (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id          UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    week_number        INTEGER NOT NULL,
    title              VARCHAR(200) NOT NULL,
    overview           TEXT,
    estimated_minutes  INTEGER,
    UNIQUE (course_id, week_number)
);

CREATE INDEX idx_weeks_course ON course_weeks(course_id);

CREATE TABLE lessons (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    week_id            UUID NOT NULL REFERENCES course_weeks(id) ON DELETE CASCADE,
    lesson_key         VARCHAR(50), -- e.g. "w1_l1", from the source content, for reference only
    title              VARCHAR(200) NOT NULL,
    order_index        INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX idx_lessons_week ON lessons(week_id);

CREATE TABLE lesson_content_blocks (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lesson_id          UUID NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
    order_index        INTEGER NOT NULL DEFAULT 0,
    block_type         VARCHAR(20) NOT NULL CHECK (block_type IN ('text', 'formula', 'example', 'diagram_suggestion')),
    heading            VARCHAR(200), -- text blocks
    body               TEXT,         -- text / example blocks
    label              VARCHAR(200), -- formula blocks
    expression         TEXT,         -- formula blocks
    explanation        TEXT          -- formula blocks
);

CREATE INDEX idx_content_blocks_lesson ON lesson_content_blocks(lesson_id);

CREATE TABLE lesson_note_anchors (
    id                     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lesson_id              UUID NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
    anchor_text            TEXT,
    suggested_note_prompt  TEXT
);

CREATE INDEX idx_note_anchors_lesson ON lesson_note_anchors(lesson_id);

CREATE TABLE week_completion_criteria (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    week_id            UUID NOT NULL REFERENCES course_weeks(id) ON DELETE CASCADE,
    criterion_text     TEXT NOT NULL,
    order_index        INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX idx_completion_criteria_week ON week_completion_criteria(week_id);

CREATE TABLE course_qa_items (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id          UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    question           TEXT NOT NULL,
    answer             TEXT NOT NULL,
    source_week        INTEGER,
    difficulty         VARCHAR(20)
);

CREATE INDEX idx_qa_items_course ON course_qa_items(course_id);

-- ---------------------------------------------------------------------------
-- user_progress — one row per (user, lesson) marking that lesson complete
-- ---------------------------------------------------------------------------
CREATE TABLE user_progress (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id            UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id          UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    week_number        INTEGER NOT NULL,
    lesson_id          UUID NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
    completed_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, lesson_id)
);

CREATE INDEX idx_progress_user_course ON user_progress(user_id, course_id);

-- ---------------------------------------------------------------------------
-- quiz_attempts — one row per attempt at a week's gating quiz
-- ---------------------------------------------------------------------------
CREATE TABLE quiz_attempts (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id            UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    week_id            UUID NOT NULL REFERENCES course_weeks(id) ON DELETE CASCADE,
    score              NUMERIC(5,2) NOT NULL DEFAULT 0,
    passed             BOOLEAN NOT NULL DEFAULT FALSE,
    answers            JSONB NOT NULL DEFAULT '{}'::jsonb,
    attempted_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_quiz_attempts_user_week ON quiz_attempts(user_id, week_id);

-- ---------------------------------------------------------------------------
-- notes — a trainee's personal note attached to a highlighted content excerpt
-- ---------------------------------------------------------------------------
CREATE TABLE notes (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id            UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    lesson_id          UUID NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
    anchor_text        TEXT,
    note_text          TEXT NOT NULL,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_notes_user_lesson ON notes(user_id, lesson_id);

-- ---------------------------------------------------------------------------
-- tutor_conversations — AI tutor chat history per user per lesson
-- ---------------------------------------------------------------------------
CREATE TABLE tutor_conversations (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id            UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    lesson_id          UUID NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
    messages           JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_tutor_conversations_user_lesson ON tutor_conversations(user_id, lesson_id);

-- ---------------------------------------------------------------------------
-- assessments (questionnaires) — created by trainers, tied to a course
-- ---------------------------------------------------------------------------
CREATE TABLE assessments (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id         UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    title             VARCHAR(200) NOT NULL,
    created_by        UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_assessments_course ON assessments(course_id);

-- ---------------------------------------------------------------------------
-- assessment_questions — mcq, true_false, fill_in_blank, or short_answer
-- ---------------------------------------------------------------------------
CREATE TYPE question_type AS ENUM ('mcq', 'true_false', 'fill_in_blank', 'short_answer');

CREATE TABLE assessment_questions (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id     UUID NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
    question_type     question_type NOT NULL DEFAULT 'mcq',
    question_text     TEXT NOT NULL,
    -- options only apply to mcq / true_false; NULL for fill_in_blank / short_answer
    option_a          VARCHAR(500),
    option_b          VARCHAR(500),
    option_c          VARCHAR(500),
    option_d          VARCHAR(500),
    -- for mcq/true_false: the correct option letter (A-D). for fill_in_blank/short_answer:
    -- the expected free-text answer, graded via a normalized (trim+lowercase) comparison.
    correct_answer    VARCHAR(500) NOT NULL,
    competency_tag    VARCHAR(120),
    -- which course week this question gates (from ai_test_questions.source_week on import);
    -- NULL for questions authored manually via the general questionnaire flow.
    source_week       INTEGER
);

CREATE INDEX idx_questions_assessment ON assessment_questions(assessment_id);
CREATE INDEX idx_questions_source_week ON assessment_questions(assessment_id, source_week);

-- ---------------------------------------------------------------------------
-- assessment_submissions — a trainee's attempt + score + answers
-- ---------------------------------------------------------------------------
CREATE TABLE assessment_submissions (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id     UUID NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
    trainee_id        UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    score             NUMERIC(5,2) NOT NULL DEFAULT 0,
    total_questions   INTEGER NOT NULL DEFAULT 0,
    answers           JSONB NOT NULL DEFAULT '{}'::jsonb, -- {question_id: "A"}
    submitted_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (assessment_id, trainee_id)
);

CREATE INDEX idx_submissions_trainee ON assessment_submissions(trainee_id);

-- ---------------------------------------------------------------------------
-- feedback — trainee feedback on a course
-- ---------------------------------------------------------------------------
CREATE TABLE feedback (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id         UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    trainee_id        UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    rating            SMALLINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comments          TEXT,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (course_id, trainee_id)
);

CREATE INDEX idx_feedback_course ON feedback(course_id);

-- ---------------------------------------------------------------------------
-- announcements — posted by admins
-- ---------------------------------------------------------------------------
CREATE TABLE announcements (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title             VARCHAR(200) NOT NULL,
    message           TEXT NOT NULL,
    created_by        UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- updated_at trigger helper
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_courses_updated_at BEFORE UPDATE ON courses
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ============================================================================
-- Seeding the first admin (required — no admin exists yet to approve one):
--
--   1. Sign up normally through the app with role="admin".
--   2. Then run, directly against the database:
--
--      UPDATE users SET is_approved = TRUE WHERE email = 'you@example.com';
--
-- Do this once; every subsequent trainer/admin signup can be approved via
-- the Admin Dashboard instead of raw SQL.
-- ============================================================================
