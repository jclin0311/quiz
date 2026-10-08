"""Daily practice and Ebbinghaus-style review scheduling. Deterministic, no LLM."""

from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from . import clock
from .models import ReviewItem

# A question first solved on day d is reviewed on d+1, d+2, d+6 and d+31.
REVIEW_OFFSETS = (1, 2, 6, 31)


def schedule_reviews(db: Session, user_id: int, plan: str, question_id: int, solved_on: date) -> None:
    """Create review items the first time a user solves a question in a plan. No-op afterwards."""
    exists = db.scalar(
        select(ReviewItem.id).where(
            ReviewItem.user_id == user_id, ReviewItem.plan == plan, ReviewItem.question_id == question_id
        )
    )
    if exists:
        return
    for stage, offset in enumerate(REVIEW_OFFSETS):
        db.add(
            ReviewItem(
                user_id=user_id,
                plan=plan,
                question_id=question_id,
                stage=stage,
                due_date=solved_on + timedelta(days=offset),
            )
        )


def due_review_question_ids(db: Session, user_id: int, plan: str, today: date) -> list[int]:
    """Questions with at least one incomplete review due today or earlier (missed days roll over)."""
    rows = db.execute(
        select(ReviewItem.question_id, ReviewItem.due_date)
        .where(
            ReviewItem.user_id == user_id,
            ReviewItem.plan == plan,
            ReviewItem.due_date <= today,
            ReviewItem.completed_at.is_(None),
        )
        .order_by(ReviewItem.due_date, ReviewItem.question_id)
    ).all()
    seen: dict[int, None] = {}
    for qid, _ in rows:
        seen.setdefault(qid, None)
    return list(seen)


def complete_due_reviews(db: Session, user_id: int, plan: str, question_id: int, today: date) -> None:
    """Answering a review clears every stage of that question that is already due."""
    items = db.scalars(
        select(ReviewItem).where(
            ReviewItem.user_id == user_id,
            ReviewItem.plan == plan,
            ReviewItem.question_id == question_id,
            ReviewItem.due_date <= today,
            ReviewItem.completed_at.is_(None),
        )
    )
    for item in items:
        item.completed_at = clock.now()
