"""
Enterprise AI Knowledge Copilot - Main FastAPI Application.

Production-grade self-hosted AI knowledge management platform
with RAG, agent workflows, prompt management, tracing, and eval.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.exceptions import AppException
from app.core.logging import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application startup/shutdown lifecycle."""
    logger.info(
        "starting_application",
        app_name=settings.app_name,
        environment=settings.app_env,
    )
    yield
    logger.info("shutting_down_application")


app = FastAPI(
    title="Enterprise AI Knowledge Copilot",
    description=(
        "Production-grade, self-hosted AI knowledge management platform with "
        "RAG retrieval, agent workflows, prompt versioning, tracing/observability, "
        "and evaluation pipelines."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ── CORS ────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Security Headers Middleware ─────────────────────────
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response


# ── Exception Handler ───────────────────────────────────
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    logger.warning(
        "app_exception",
        status_code=exc.status_code,
        message=exc.message,
        path=str(request.url),
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "detail": exc.detail,
            "status_code": exc.status_code,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(
        "unhandled_exception",
        error=str(exc),
        path=str(request.url),
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.debug else None,
            "status_code": 500,
        },
    )


# ── Routes ──────────────────────────────────────────────
from app.api.routes import auth, organizations, chat, knowledge, prompts, traces, evaluation, feedback, audit, admin  # noqa: E402

app.include_router(auth.router, prefix="/api/v1")
app.include_router(organizations.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(knowledge.router, prefix="/api/v1")
app.include_router(prompts.router, prefix="/api/v1")
app.include_router(traces.router, prefix="/api/v1")
app.include_router(evaluation.router, prefix="/api/v1")
app.include_router(feedback.router, prefix="/api/v1")
app.include_router(audit.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")


# ── Health Check ────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "version": "1.0.0",
        "environment": settings.app_env,
    }


@app.get("/", tags=["Root"])
async def root():
    return {
        "name": "Enterprise AI Knowledge Copilot",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }
