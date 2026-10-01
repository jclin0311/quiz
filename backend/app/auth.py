import hashlib
import secrets
from datetime import timedelta

from fastapi import Cookie, Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import clock
from .config import SESSION_COOKIE, settings
from .db import get_db
from .models import AuthSession, User


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def verify_google_credential(credential: str) -> dict:
    """Validate a Google Identity Services ID token and return its claims."""
    from google.auth.transport import requests as google_requests
    from google.oauth2 import id_token

    if not settings.google_client_id:
        raise HTTPException(503, "Google sign-in unavailable")
    try:
        claims = id_token.verify_oauth2_token(
            credential, google_requests.Request(), settings.google_client_id
        )
    except ValueError as exc:
        raise HTTPException(401, "Sign-in failed") from exc
    if not claims.get("email_verified", False):
        raise HTTPException(401, "Email not verified")
    return claims


def issue_session(db: Session, response: Response, user: User) -> None:
    token = secrets.token_urlsafe(32)
    db.add(
        AuthSession(
            user_id=user.id,
            token_hash=_hash(token),
            expires_at=clock.now() + timedelta(days=settings.session_days),
        )
    )
    db.commit()
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=settings.session_days * 86400,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
        path="/",
    )


def revoke_session(db: Session, response: Response, token: str | None) -> None:
    if token:
        row = db.scalar(select(AuthSession).where(AuthSession.token_hash == _hash(token)))
        if row and row.revoked_at is None:
            row.revoked_at = clock.now()
            db.commit()
    response.delete_cookie(SESSION_COOKIE, path="/")


def current_user(
    request: Request,
    db: Session = Depends(get_db),
    token: str | None = Cookie(default=None, alias=SESSION_COOKIE),
) -> User:
    # Mutating requests must carry a custom header. Browsers cannot attach it
    # cross-origin without a CORS preflight, which this API never grants.
    if request.method not in {"GET", "HEAD", "OPTIONS"} and request.headers.get("x-requested-with") != "quiz":
        raise HTTPException(403, "Forbidden")
    if not token:
        raise HTTPException(401, "Signed out")
    row = db.scalar(select(AuthSession).where(AuthSession.token_hash == _hash(token)))
    if row is None or row.revoked_at is not None or _aware(row.expires_at) < clock.now():
        raise HTTPException(401, "Signed out")
    user = db.get(User, row.user_id)
    if user is None:
        raise HTTPException(401, "Signed out")
    return user


def _aware(dt):
    # SQLite drops tzinfo; values are always stored as UTC.
    from datetime import timezone

    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
