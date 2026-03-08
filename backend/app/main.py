from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db
from app.routers import admin, auth, faculty, student


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialise the database (create tables + seed demo users) on startup."""
    init_db()
    yield


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
        description=(
            "REST API backend for the AI Student Performance Dashboard.\n\n"
            "**Default credentials (demo)**\n\n"
            "| Role | Email | Password |\n"
            "|---|---|---|\n"
            "| Faculty | sarah@university.edu | faculty123 |\n"
            "| Student | alex@university.edu  | student123 |"
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # ── CORS ──────────────────────────────────────────────────────────────────
    _cors_origins = sorted(
        {
            *settings.cors_origins,
            "http://localhost:5173", "http://127.0.0.1:5173",
            "http://localhost:5174", "http://127.0.0.1:5174",
            "http://localhost:5175", "http://127.0.0.1:5175",
            "http://localhost:3000", "http://127.0.0.1:3000",
        }
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins,
        # Be permissive for local dev ports (fixes "Failed to fetch" if Vite picks a new port).
        allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routers ───────────────────────────────────────────────────────────────
    app.include_router(auth.router,    prefix="/api/v1")
    app.include_router(admin.router,   prefix="/api/v1")
    app.include_router(faculty.router, prefix="/api/v1")
    app.include_router(student.router, prefix="/api/v1")

    # ── Health check ──────────────────────────────────────────────────────────
    @app.get("/health", tags=["Health"], summary="Server health check")
    def health() -> dict:
        return {"status": "ok", "version": settings.app_version}

    return app


app = create_app()
