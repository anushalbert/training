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
-- assessment_questions — MCQ questions
-- ---------------------------------------------------------------------------
CREATE TABLE assessment_questions (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id     UUID NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
    question_text     TEXT NOT NULL,
    option_a          VARCHAR(500) NOT NULL,
    option_b          VARCHAR(500) NOT NULL,
    option_c          VARCHAR(500) NOT NULL,
    option_d          VARCHAR(500) NOT NULL,
    correct_option    CHAR(1) NOT NULL CHECK (correct_option IN ('A', 'B', 'C', 'D')),
    competency_tag    VARCHAR(120)
);

CREATE INDEX idx_questions_assessment ON assessment_questions(assessment_id);

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
