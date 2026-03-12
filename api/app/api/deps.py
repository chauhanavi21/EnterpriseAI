"""
FastAPI dependencies: auth, database, rate limiting.
"""
from __future__ import annotations

import time
import uuid
from collections import defaultdict
from typing import Optional

from fastapi import Depends, Header, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import RateLimitError, UnauthorizedError
from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User
from app.services.user_service import UserService

security_scheme = HTTPBearer(auto_error=False)

# Simple in-memory rate limiter (use Redis in production)
_rate_limit_store: dict[str, list[float]] = defaultdict(list)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extract and validate the current user from JWT token."""
    if not credentials:
        raise UnauthorizedError("Missing authentication token")

    try:
        payload = decode_token(credentials.credentials)
    except ValueError as e:
        raise UnauthorizedError(str(e))

    if payload.get("type") != "access":
        raise UnauthorizedError("Invalid token type")

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedError("Invalid token payload")

    service = UserService(db)
    try:
        user = await service.get_by_id(uuid.UUID(user_id))
    except Exception:
        raise UnauthorizedError("User not found")

    if not user.is_active:
        raise UnauthorizedError("User account is deactivated")

    return user


async def get_current_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """Require superuser role."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Superuser access required")
    return current_user


def rate_limit(request: Request):
    """Simple rate limiter middleware."""
    settings = get_settings()
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    window = 60  # 1 minute

    # Clean old entries
    _rate_limit_store[client_ip] = [
        t for t in _rate_limit_store[client_ip] if now - t < window
    ]

    if len(_rate_limit_store[client_ip]) >= settings.rate_limit_per_minute:
        raise RateLimitError()

    _rate_limit_store[client_ip].append(now)
