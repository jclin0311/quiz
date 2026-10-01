import random
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from .. import clock
from ..auth import current_user
from ..clock import local_today
from ..db import get_db
from ..mastery import recompute_user_mastery
from ..models import Attempt, Choice, Company, Question, QuestionCompany, QuizSession, Topic, User
from ..recommend import recommend
from ..scheduling import complete_due_reviews, due_review_question_ids, schedule_reviews

router = APIRouter(prefix="/api/sessions", tags=["quiz"])

EXTRA_SIZE = 5


class CreateSession(BaseModel):
    mode: Literal["daily", "review", "extra"]


class AnswerBody(BaseModel):
    question_id: int
    choice_id: int


def _owned_session(db: Session, user: User, session_id: int) -> QuizSession:
    session = db.get(QuizSession, session_id)
    if session is None or session.user_id != user.id:
        raise HTTPException(404, "Not found")
    return session


def _new_session(db: Session, user: User, mode: str, today, qids: list[int], reasons: dict[str, str]) -> QuizSession:
    rng = random.SystemRandom()
    orders = {}
    for qid in qids:
        choice_ids = list(db.scalars(select(Choice.id).where(Choice.question_id == qid)))
        rng.shuffle(choice_ids)
        orders[str(qid)] = choice_ids
    session = QuizSession(
        user_id=user.id, mode=mode, local_date=today, question_ids=qids, choice_orders=orders, reasons=reasons
    )
    db.add(session)
    db.commit()
    return session


def _feedback(question: Question, chosen_id: int) -> dict:
    correct = next(c for c in question.choices if c.verdict == "optimal")
    return {
        "choice_id": chosen_id,
        "is_correct": chosen_id == correct.id,
        "correct_choice_id": correct.id,
        "feedback": [
            {"choice_id": c.id, "verdict": c.verdict, "explanation": c.explanation} for c in question.choices
        ],
    }


def session_payload(db: Session, session: QuizSession) -> dict:
    questions = {
        q.id: q
        for q in db.scalars(
            select(Question)
            .where(Question.id.in_(session.question_ids))
            .options(selectinload(Question.choices), selectinload(Question.topics))
        )
    }
    topic_names = {tid: name for tid, name in db.execute(select(Topic.id, Topic.name))}
    tags: dict[int, list[dict]] = {}
    for qc, name in db.execute(
        select(QuestionCompany, Company.name)
        .join(Company, Company.id == QuestionCompany.company_id)
        .where(QuestionCompany.question_id.in_(session.question_ids))
    ):
        tags.setdefault(qc.question_id, []).append(
            {"company": name, "provenance": qc.provenance,
             "observed_on": qc.observed_on.isoformat() if qc.observed_on else None}
        )
    answers = {a.question_id: a for a in db.scalars(select(Attempt).where(Attempt.session_id == session.id))}

    items = []
    for qid in session.question_ids:
        q = questions[qid]
        by_id = {c.id: c for c in q.choices}
        attempt = answers.get(qid)
        items.append(
            {
                "question": {
                    "id": q.id,
                    "title": q.title,
                    "lc_number": q.lc_number,
                    "difficulty": q.difficulty,
                    "summary": q.summary,
                    "example": q.example,
                    "criterion": q.criterion,
                    "hint": q.hint,
                    "source_url": q.source_url,
                    "topics": [{"id": t.topic_id, "name": topic_names[t.topic_id]} for t in q.topics],
                    "company_tags": tags.get(q.id, []),
                },
                "reason": session.reasons.get(str(qid)),
                # Answer-free payload: verdicts and explanations only arrive after answering.
                "choices": [
                    {
                        "id": by_id[cid].id,
                        "label": by_id[cid].label,
                        "detail": by_id[cid].detail,
                        "time": by_id[cid].time_complexity,
                        "space": by_id[cid].space_complexity,
                        "visual": by_id[cid].visual,
                    }
                    for cid in session.choice_orders[str(qid)]
                ],
                "result": _feedback(q, attempt.choice_id) if attempt else None,
            }
        )
    return {
        "id": session.id,
        "mode": session.mode,
        "local_date": session.local_date.isoformat(),
        "finished": session.finished_at is not None,
        "items": items,
    }


@router.post("")
def create_session(body: CreateSession, user: User = Depends(current_user), db: Session = Depends(get_db)):
    today = local_today(user.timezone)
    if body.mode in ("daily", "review"):
        existing = db.scalar(
            select(QuizSession).where(
                QuizSession.user_id == user.id,
                QuizSession.mode == body.mode,
                QuizSession.local_date == today,
            )
        )
        if existing:
            return session_payload(db, existing)

    if body.mode == "review":
        qids = due_review_question_ids(db, user.id, today)
        if not qids:
            raise HTTPException(409, "Nothing to review")
        session = _new_session(db, user, "review", today, qids, {str(q): "Review" for q in qids})
    else:
        limit = user.daily_goal if body.mode == "daily" else EXTRA_SIZE
        picks = recommend(db, user.id, today, limit, purpose=body.mode)
        if not picks:
            raise HTTPException(409, "No questions left")
        session = _new_session(
            db, user, body.mode, today, [p.question_id for p in picks], {str(p.question_id): p.reason for p in picks}
        )
    return session_payload(db, session)


@router.get("/{session_id}")
def get_session(session_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return session_payload(db, _owned_session(db, user, session_id))


@router.post("/{session_id}/answer")
def answer(session_id: int, body: AnswerBody, user: User = Depends(current_user), db: Session = Depends(get_db)):
    session = _owned_session(db, user, session_id)
    if body.question_id not in session.question_ids:
        raise HTTPException(400, "Invalid question")
    question = db.scalar(
        select(Question).where(Question.id == body.question_id).options(selectinload(Question.choices))
    )
    if body.choice_id not in {c.id for c in question.choices}:
        raise HTTPException(400, "Invalid choice")

    existing = db.scalar(
        select(Attempt).where(Attempt.session_id == session.id, Attempt.question_id == question.id)
    )
    if existing:  # idempotent: the first submission wins
        return _feedback(question, existing.choice_id)

    today = local_today(user.timezone)
    result = _feedback(question, body.choice_id)
    db.add(
        Attempt(
            user_id=user.id,
            session_id=session.id,
            question_id=question.id,
            choice_id=body.choice_id,
            is_correct=result["is_correct"],
            mode=session.mode,
            local_date=today,
        )
    )
    if session.mode == "review":
        complete_due_reviews(db, user.id, question.id, today)
    else:
        schedule_reviews(db, user.id, question.id, today)
    try:
        db.commit()
    except IntegrityError:  # concurrent duplicate submit
        db.rollback()
        existing = db.scalar(
            select(Attempt).where(Attempt.session_id == session.id, Attempt.question_id == question.id)
        )
        return _feedback(question, existing.choice_id)
    return result


@router.post("/{session_id}/finish")
def finish(session_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Called when the learner leaves or completes a quiz; refreshes mastery."""
    session = _owned_session(db, user, session_id)
    answered = db.scalar(select(func.count()).select_from(Attempt).where(Attempt.session_id == session.id))
    correct = db.scalar(
        select(func.count())
        .select_from(Attempt)
        .where(Attempt.session_id == session.id, Attempt.is_correct.is_(True))
    )
    if answered == len(session.question_ids) and session.finished_at is None:
        session.finished_at = clock.now()
        db.commit()
    recompute_user_mastery(db, user.id)
    return {"total": len(session.question_ids), "answered": answered, "correct": correct,
            "finished": session.finished_at is not None}
