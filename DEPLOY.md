# Deploying to a live URL (Render + Supabase, both free tier)

This deploys the real app — FastAPI backend, React frontend, Postgres database —
to actual hosted URLs. No credit card required for either service's free tier
as of this writing. Total time: ~15 minutes, all done in your browser.

Why this combo: Render's free Postgres expires after a set period; Supabase's
free Postgres does not. The repo's `db/schema.sql` and `supabase/config.toml`
were already written with Supabase in mind.

---

## Step 1 — Push this repo to GitHub

```bash
cd training-platform
git init
git add .
git commit -m "Initial training platform scaffold"
```

Then create a new empty repo on https://github.com/new (don't initialize it
with a README), and push:

```bash
git remote add origin https://github.com/<your-username>/training-platform.git
git branch -M main
git push -u origin main
```

## Step 2 — Create the database (Supabase)

1. Go to https://supabase.com → New project (free tier).
2. Once it's provisioned, open **SQL Editor** → paste the contents of
   `db/schema.sql` → Run. This creates all tables/enums/triggers.
3. Go to **Project Settings → Database → Connection string** → copy the
   **URI** (use the "Session pooler" connection string if given the choice —
   works better with serverless/free-tier backend hosts).
4. It looks like `postgresql://postgres:[PASSWORD]@...:5432/postgres`.
   Change the scheme prefix from `postgresql://` to `postgresql+psycopg2://`
   (SQLAlchemy needs the driver name). Save this — it's your `DATABASE_URL`.

## Step 3 — Deploy backend + frontend (Render)

1. Go to https://render.com → sign up / log in (e.g. with GitHub).
2. **New → Blueprint** → connect your GitHub account → select the
   `training-platform` repo. Render will detect `render.yaml` at the repo
   root and propose two services: `training-platform-backend` and
   `training-platform-frontend`. Click **Apply**.
3. Render will prompt for the `sync: false` env vars it can't guess:
   - On **training-platform-backend**: paste `DATABASE_URL` from Step 2.
     Leave `CORS_ORIGINS` blank for now — you'll fill it in after Step 3.5.
   - On **training-platform-frontend**: leave `VITE_API_URL` blank for now too.
4. Let the backend service finish deploying. Copy its URL, e.g.
   `https://training-platform-backend.onrender.com`.
5. Go to **training-platform-frontend → Environment**, set:
   `VITE_API_URL = https://training-platform-backend.onrender.com/api`
   Save — this triggers a rebuild (Vite bakes the URL in at build time).
6. Once the frontend finishes deploying, copy its URL, e.g.
   `https://training-platform-frontend.onrender.com`.
7. Go back to **training-platform-backend → Environment**, set:
   `CORS_ORIGINS = https://training-platform-frontend.onrender.com`
   Save — this triggers a backend redeploy.

Render's free web services spin down after ~15 minutes idle — the first
request after idle takes 30-60s to wake up. That's expected on the free tier.

## Step 4 — Create your first admin

1. Open your frontend URL → **Sign up** → role = Admin.
2. In Supabase → SQL Editor, run:
   ```sql
   UPDATE users SET is_approved = TRUE WHERE email = 'you@example.com';
   ```
3. Log in as that admin. From here on, approve any further trainer/admin
   signups from the Admin Dashboard → Approvals tab instead of raw SQL.

## Step 5 — Smoke test

- Sign up a trainee (auto-approved) → log in → enroll in a course (create one
  as trainer/admin first) → take an assessment → leave feedback.
- Sign up a trainer → approve via admin → create a course, add competencies,
  upload a material link, build a questionnaire.
- Confirm Admin → Stats reflects the activity, and Course Assignment surfaces
  the trainer via competency match.

---

## Updating after code changes

Render auto-redeploys both services on every push to `main`:

```bash
git add -A
git commit -m "your change"
git push
```

## Alternative hosts

Any Docker-capable host works for the backend (Railway, Fly.io, a VPS) and
any static host works for the frontend (Vercel, Netlify, Cloudflare Pages) —
same env vars apply (`DATABASE_URL`/`JWT_SECRET`/`CORS_ORIGINS` on the
backend, `VITE_API_URL` on the frontend). `render.yaml` is Render-specific;
other hosts don't need it.
