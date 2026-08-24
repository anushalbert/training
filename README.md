# Training Platform

A full-stack training/LMS platform with three roles: **Trainee**, **Trainer**, **Admin**.

## Stack
- **Backend**: FastAPI (Python), SQLAlchemy, JWT (python-jose), bcrypt (passlib)
- **Database**: PostgreSQL (Supabase-compatible)
- **Frontend**: React (Vite), React Router, Axios
- **Deployment**: Docker + docker-compose, Supabase config

## Folder Structure
```
training-platform/
├── db/
│   └── schema.sql              # Full PostgreSQL schema (run on Supabase or local Postgres)
├── backend/                    # FastAPI REST API
│   └── app/
│       ├── core/               # config, security (JWT/bcrypt), db session
│       ├── models/             # SQLAlchemy ORM models
│       ├── schemas/            # Pydantic request/response schemas
│       ├── api/routes/         # REST endpoints
│       └── services/           # business logic (competency mapping, etc.)
├── frontend/                   # React SPA
│   └── src/
│       ├── api/                # axios client + API calls
│       ├── context/            # AuthContext (JWT storage, role)
│       ├── routes/             # ProtectedRoute (role-based guard)
│       ├── pages/admin|trainer|trainee/
│       └── components/
├── supabase/
│   └── config.toml             # Supabase local dev config
├── docker-compose.yml
└── .env.example
```

## 1. Database setup

**Option A — Local Postgres via Docker Compose** (default, see below).

**Option B — Supabase**: create a project at supabase.com, then run `db/schema.sql`
in the Supabase SQL editor. Copy your project's connection string into
`backend/.env` as `DATABASE_URL`.

## 2. Backend — run locally

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # edit DATABASE_URL, JWT_SECRET
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

## 3. Frontend — run locally

```bash
cd frontend
npm install
cp .env.example .env            # edit VITE_API_URL if needed
npm run dev
```

App: http://localhost:5173

## 4. Run everything with Docker Compose

```bash
docker compose up --build
```

This starts: Postgres (5432), backend (8000), frontend (5173).

## 5. Default roles & approval flow

- **Signup** creates a user with the role they choose (`trainee`, `trainer`, `admin`).
- `trainee` accounts are **auto-approved**.
- `trainer` and `admin` accounts start as `is_approved = false` and must be
  approved by an existing admin via `PATCH /api/admin/users/{id}/approve`
  (Admin Dashboard → Approvals tab in the UI).
- Seed the very first admin directly in the database (see `db/schema.sql`
  bottom comment) since no admin exists yet to approve one.

## 6. Competency mapping

Trainers declare competencies (skill + proficiency level) in
`trainer_competencies`. Courses declare required competencies in
`course_competencies`. `POST /api/admin/courses/{id}/suggest-trainers`
(and the equivalent service function `suggest_trainers_for_course`)
scores every trainer by overlap + proficiency against the course's
required competencies and returns a ranked list, so an admin can assign
the best-fit trainer to a course.

## Security notes
- Passwords hashed with bcrypt (passlib), never stored/returned in plaintext.
- JWT access tokens (HS256), short expiry, role embedded in claims, verified
  server-side on every protected route via FastAPI dependencies.
- All mutating admin/trainer endpoints check role **and** approval status
  server-side (not just hidden in the UI).
