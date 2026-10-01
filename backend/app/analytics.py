"""Deterministic performance statistics — the source of truth for charts and narrative."""

from collections import defaultdict
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from .mastery import mastery_map
from .models import Attempt, QuestionTopic, Topic

DAYS = 30
WEEKS = 8


def week_start(d: date) -> date:
    return d - timedelta(days=d.weekday())


def streak(db: Session, user_id: int, today: date) -> int:
    days = set(db.scalars(select(Attempt.local_date).where(Attempt.user_id == user_id).distinct()))
    # A streak survives until the end of today even if today has no practice yet.
    d = today if today in days else today - timedelta(days=1)
    count = 0
    while d in days:
        count += 1
        d -= timedelta(days=1)
    return count


def dashboard_stats(db: Session, user_id: int, today: date) -> dict:
    topics = list(db.scalars(select(Topic).order_by(Topic.position)))
    names = {t.id: t.name for t in topics}
    rows = db.execute(
        select(Attempt.local_date, Attempt.is_correct, Attempt.mode, QuestionTopic.topic_id)
        .join(QuestionTopic, QuestionTopic.question_id == Attempt.question_id)
        .where(Attempt.user_id == user_id, QuestionTopic.is_primary.is_(True))
    ).all()

    by_topic: dict[str, list[int]] = defaultdict(lambda: [0, 0])  # [attempts, correct]
    by_day: dict[date, list[int]] = defaultdict(lambda: [0, 0])
    by_topic_week: dict[tuple[str, date], list[int]] = defaultdict(lambda: [0, 0])
    for d, ok, _mode, topic_id in rows:
        for bucket in (by_topic[topic_id], by_day[d], by_topic_week[(topic_id, week_start(d))]):
            bucket[0] += 1
            bucket[1] += int(ok)

    def pct(a: int, c: int) -> float | None:
        return round(100 * c / a, 1) if a else None

    topic_accuracy = [
        {"topic": t.id, "name": t.name, "attempts": by_topic[t.id][0], "correct": by_topic[t.id][1],
         "accuracy": pct(*by_topic[t.id])}
        for t in topics
        if by_topic[t.id][0]
    ]

    start = today - timedelta(days=DAYS - 1)
    per_day = []
    for i in range(DAYS):
        d = start + timedelta(days=i)
        a, c = by_day.get(d, (0, 0))
        per_day.append({"date": d.isoformat(), "answered": a, "correct": c})

    weeks = [week_start(today) - timedelta(weeks=WEEKS - 1 - i) for i in range(WEEKS)]
    weekly = {}
    for t in topics:
        series = []
        for w in weeks:
            a, c = by_topic_week.get((t.id, w), (0, 0))
            series.append({"week": w.isoformat(), "attempts": a, "accuracy": pct(a, c)})
        if any(s["attempts"] for s in series):
            weekly[t.id] = series

    total = sum(v[0] for v in by_topic.values())
    correct = sum(v[1] for v in by_topic.values())
    this_week = [s for (tid, w), s in by_topic_week.items() if w == week_start(today)]
    last_week = [s for (tid, w), s in by_topic_week.items() if w == week_start(today) - timedelta(weeks=1)]

    mastery = mastery_map(db, user_id)
    return {
        "totals": {
            "answered": total,
            "correct": correct,
            "accuracy": pct(total, correct),
            "active_days": sum(1 for v in by_day.values() if v[0]),
            "streak": streak(db, user_id, today),
            "this_week_answered": sum(s[0] for s in this_week),
            "this_week_accuracy": pct(sum(s[0] for s in this_week), sum(s[1] for s in this_week)),
            "last_week_answered": sum(s[0] for s in last_week),
            "last_week_accuracy": pct(sum(s[0] for s in last_week), sum(s[1] for s in last_week)),
        },
        "topic_accuracy": topic_accuracy,
        "per_day": per_day,
        "weekly_topic_accuracy": weekly,
        "mastery": {
            tid: {"name": names[tid], "mastery": round(m.mastery * 100, 1), "attempts": m.attempts}
            for tid, m in mastery.items()
        },
    }
