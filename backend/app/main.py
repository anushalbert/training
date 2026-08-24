from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import Base, engine
from app.models import *  # noqa: F401,F403  — ensures all models are registered on Base
from app.api.routes import auth, users, courses, materials, assessments, feedback, announcements, admin, content

app = FastAPI(title="Training Platform API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    # For local/dev convenience only. In production, run db/schema.sql (or a
    # migration tool like Alembic) explicitly instead of relying on this.
    Base.metadata.create_all(bind=engine)


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(courses.router)
app.include_router(materials.router)
app.include_router(assessments.router)
app.include_router(feedback.router)
app.include_router(announcements.router)
app.include_router(admin.router)
app.include_router(content.router)


@app.get("/api/health", tags=["health"])
def health_check():
    return {"status": "ok"}
