from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..analytics import streak
from ..auth import current_user
from ..clock import local_today, valid_timezone
from ..db import get_db
from ..models import Attempt, QuizSession, User
from ..scheduling import due_review_question_ids

router = APIRouter(prefix="/api", tags=["profile"])


class ProfileUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=40)
    timezone: str | None = None
    daily_goal: int | None = Field(default=None, ge=1, le=20)


def user_payload(user: User) -> dict:
    return {
        "id": user.id,
        "name": user.name,
        "display_name": user.display_name or user.name,
        "email": user.email,
        "avatar_url": user.avatar_url,
        "timezone": user.timezone,
        "daily_goal": user.daily_goal,
    }


@router.get("/me")
def get_me(user: User = Depends(current_user)):
    return user_payload(user)


@router.patch("/me")
def update_me(body: ProfileUpdate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if body.display_name is not None:
        name = body.display_name.strip()
        if not name:
            raise HTTPException(422, "Name required")
        user.display_name = name
    if body.timezone is not None:
        if not valid_timezone(body.timezone):
            raise HTTPException(422, "Unknown timezone")
        user.timezone = body.timezone
    if body.daily_goal is not None:
        user.daily_goal = body.daily_goal
    db.commit()
    return user_payload(user)


def _progress(db: Session, session: QuizSession | None) -> dict | None:
    if session is None:
        return None
    answered = db.scalar(
        select(func.count()).select_from(Attempt).where(Attempt.session_id == session.id)
    )
    correct = db.scalar(
        select(func.count())
        .select_from(Attempt)
        .where(Attempt.session_id == session.id, Attempt.is_correct.is_(True))
    )
    return {
        "session_id": session.id,
        "mode": session.mode,
        "total": len(session.question_ids),
        "answered": answered,
        "correct": correct,
    }


@router.get("/home")
def home(user: User = Depends(current_user), db: Session = Depends(get_db)):
    today = local_today(user.timezone)
    sessions = list(
        db.scalars(
            select(QuizSession)
            .where(QuizSession.user_id == user.id, QuizSession.local_date == today)
            .order_by(QuizSession.id)
        )
    )
    daily = next((s for s in sessions if s.mode == "daily"), None)
    review = next((s for s in sessions if s.mode == "review"), None)
    extras = [s for s in sessions if s.mode == "extra"]

    progress = [p for p in (_progress(db, s) for s in sessions) if p]
    unfinished = next((p for p in reversed(progress) if 0 < p["answered"] < p["total"]), None)

    return {
        "user": user_payload(user),
        "today": today.isoformat(),
        "streak": streak(db, user.id, today),
        "daily": _progress(db, daily) or {"session_id": None, "total": user.daily_goal, "answered": 0, "correct": 0},
        "review": _progress(db, review)
        or {"session_id": None, "total": len(due_review_question_ids(db, user.id, today)), "answered": 0, "correct": 0},
        "extra": [_progress(db, s) for s in extras],
        "resume": unfinished,
    }
