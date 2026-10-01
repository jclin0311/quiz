"""Topic mastery: recency-weighted, smoothed accuracy per topic."""

from collections import defaultdict

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from . import clock
from .models import Attempt, QuestionTopic, UserTopicMastery

RECENT_WINDOW = 20  # attempts per topic that count toward mastery
DECAY = 0.9  # weight multiplier per older attempt
READY_MASTERY = 0.65
READY_ATTEMPTS = 3


def compute_mastery(outcomes_newest_first: list[bool]) -> tuple[float, float]:
    """Return (mastery, confidence) for a topic.

    mastery is a Beta(1,1)-smoothed, recency-weighted accuracy, so a single
    lucky answer does not read as mastery. confidence grows with evidence.
    """
    recent = outcomes_newest_first[:RECENT_WINDOW]
    weight_sum = 0.0
    correct_sum = 0.0
    for i, ok in enumerate(recent):
        w = DECAY**i
        weight_sum += w
        correct_sum += w * ok
    mastery = (correct_sum + 1) / (weight_sum + 2)
    n = len(outcomes_newest_first)
    confidence = n / (n + 5)
    return round(mastery, 4), round(confidence, 4)


def recompute_user_mastery(db: Session, user_id: int) -> None:
    rows = db.execute(
        select(QuestionTopic.topic_id, Attempt.is_correct)
        .join(QuestionTopic, QuestionTopic.question_id == Attempt.question_id)
        .where(Attempt.user_id == user_id)
        .order_by(Attempt.created_at.desc(), Attempt.id.desc())
    ).all()
    by_topic: dict[str, list[bool]] = defaultdict(list)
    for topic_id, ok in rows:
        by_topic[topic_id].append(bool(ok))

    db.execute(delete(UserTopicMastery).where(UserTopicMastery.user_id == user_id))
    for topic_id, outcomes in by_topic.items():
        mastery, confidence = compute_mastery(outcomes)
        db.add(
            UserTopicMastery(
                user_id=user_id,
                topic_id=topic_id,
                attempts=len(outcomes),
                correct=sum(outcomes),
                mastery=mastery,
                confidence=confidence,
                updated_at=clock.now(),
            )
        )
    db.commit()


def mastery_map(db: Session, user_id: int) -> dict[str, UserTopicMastery]:
    return {
        m.topic_id: m
        for m in db.scalars(select(UserTopicMastery).where(UserTopicMastery.user_id == user_id))
    }


def is_ready(m: UserTopicMastery | None) -> bool:
    return m is not None and m.mastery >= READY_MASTERY and m.attempts >= READY_ATTEMPTS
