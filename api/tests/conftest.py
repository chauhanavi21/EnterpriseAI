"""
Shared test fixtures and configuration for pytest.
"""
import asyncio
import os
import uuid
from datetime import datetime, timedelta
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

# Patch env vars before importing app modules
os.environ.update({
    "APP_ENV": "test",
    "DATABASE_URL": "sqlite+aiosqlite:///./test.db",
    "REDIS_URL": "redis://localhost:6379/1",
    "JWT_SECRET_KEY": "test-secret-key-for-testing-only-change-in-prod",
    "CORS_ORIGINS": "http://localhost:3000",
    "OPENAI_API_KEY": "",
    "LANGFUSE_SECRET_KEY": "",
    "LANGFUSE_PUBLIC_KEY": "",
})

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.core.security import hash_password, create_access_token


# ── Async engine for tests (SQLite in-memory) ──────────
TEST_DATABASE_URL = "sqlite+aiosqlite://"

engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ── DB fixtures ────────────────────────────────────────
@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """Create all tables before each test, drop after."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


# ── Override FastAPI dependency ─────────────────────────
async def override_get_db():
    async with TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


# ── HTTP client ────────────────────────────────────────
@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ── User fixtures ──────────────────────────────────────
@pytest.fixture
def user_data():
    return {
        "email": f"test-{uuid.uuid4().hex[:8]}@test.com",
        "password": "StrongPass123!",
        "full_name": "Test User",
    }


@pytest.fixture
def admin_data():
    return {
        "email": f"admin-{uuid.uuid4().hex[:8]}@test.com",
        "password": "AdminPass123!",
        "full_name": "Admin User",
    }


@pytest_asyncio.fixture
async def registered_user(client: AsyncClient, user_data: dict):
    """Register a user and return the user_data + tokens."""
    resp = await client.post("/api/v1/auth/register", json=user_data)
    assert resp.status_code == 201
    # Login to get tokens
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": user_data["email"], "password": user_data["password"]},
    )
    assert resp.status_code == 200
    tokens = resp.json()
    return {**user_data, **tokens}


@pytest_asyncio.fixture
async def auth_headers(registered_user: dict):
    """Return Authorization headers for an authenticated user."""
    return {"Authorization": f"Bearer {registered_user['access_token']}"}


# ── Helper functions ───────────────────────────────────
def make_uuid() -> str:
    return str(uuid.uuid4())


def make_future_datetime(hours: int = 1) -> datetime:
    return datetime.utcnow() + timedelta(hours=hours)
