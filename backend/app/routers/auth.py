from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import issue_session, revoke_session, verify_google_credential
from ..clock import valid_timezone
from ..config import SESSION_COOKIE, settings
from ..db import get_db
from ..models import User

router = APIRouter(prefix="/api/auth", tags=["auth"])

DEV_SUB = "dev:demo-learner"


class GoogleLogin(BaseModel):
    credential: str
    timezone: str | None = None


class DevLogin(BaseModel):
    timezone: str | None = None


def _require_csrf_header(request: Request) -> None:
    if request.headers.get("x-requested-with") != "quiz":
        raise HTTPException(403, "Forbidden")


@router.get("/config")
def auth_config():
    return {"google_client_id": settings.google_client_id or None, "dev_login": settings.allow_dev_login}


@router.post("/google", dependencies=[Depends(_require_csrf_header)])
def google_login(body: GoogleLogin, response: Response, db: Session = Depends(get_db)):
    claims = verify_google_credential(body.credential)
    user = db.scalar(select(User).where(User.google_sub == claims["sub"]))
    if user is None:
        user = User(
            google_sub=claims["sub"],
            display_name=(claims.get("given_name") or claims.get("name") or "Learner")[:80],
            timezone=body.timezone if body.timezone and valid_timezone(body.timezone) else "UTC",
        )
        db.add(user)
    user.email = claims.get("email")
    user.name = claims.get("name", "")
    user.avatar_url = claims.get("picture")
    db.commit()
    issue_session(db, response, user)
    return {"ok": True}


@router.post("/dev", dependencies=[Depends(_require_csrf_header)])
def dev_login(body: DevLogin, response: Response, db: Session = Depends(get_db)):
    if not settings.allow_dev_login:
        raise HTTPException(404, "Not found.")
    user = db.scalar(select(User).where(User.google_sub == DEV_SUB))
    if user is None:
        user = User(
            google_sub=DEV_SUB,
            name="Demo Learner",
            display_name="Demo Learner",
            timezone=body.timezone if body.timezone and valid_timezone(body.timezone) else "UTC",
        )
        db.add(user)
        db.commit()
    issue_session(db, response, user)
    return {"ok": True}


@router.post("/logout", dependencies=[Depends(_require_csrf_header)])
def logout(
    response: Response,
    db: Session = Depends(get_db),
    token: str | None = Cookie(default=None, alias=SESSION_COOKIE),
):
    revoke_session(db, response, token)
    return {"ok": True}
