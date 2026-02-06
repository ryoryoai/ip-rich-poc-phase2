"""API dependency injection."""

from typing import Generator, Any

import httpx
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """Dependency that provides a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _get_supabase_api_key() -> str:
    """Return the API key used to call Supabase Auth endpoints."""
    api_key = settings.supabase_anon_key or settings.supabase_service_role_key
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Supabase API key is not configured",
        )
    return api_key


def get_current_user(
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    """Validate Supabase access token and return the user payload."""
    if not settings.auth_enabled:
        return {"app_metadata": {"approved": True, "role": "admin"}}

    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing access token",
        )

    if not settings.supabase_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Supabase URL is not configured",
        )

    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing access token",
        )

    url = f"{settings.supabase_url}/auth/v1/user"
    headers = {
        "Authorization": f"Bearer {token}",
        "apikey": _get_supabase_api_key(),
    }

    try:
        response = httpx.get(url, headers=headers, timeout=10.0)
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code in {401, 403}:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid access token",
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Supabase auth request failed",
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Supabase auth request failed",
        ) from exc

    return response.json()


def require_approved_user(
    user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Ensure the user has been approved (or is an admin)."""
    if not settings.auth_enabled:
        return user

    app_metadata = user.get("app_metadata") or {}
    if app_metadata.get("role") == "admin" or app_metadata.get("approved") is True:
        return user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="User is pending approval",
    )


def require_admin_user(
    user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Ensure the user is an admin."""
    if not settings.auth_enabled:
        return user

    app_metadata = user.get("app_metadata") or {}
    if app_metadata.get("role") == "admin":
        return user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Admin access required",
    )
