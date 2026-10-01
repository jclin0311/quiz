"""Deterministic question recommendation over the topic prerequisite graph.

1. Pick target topics: weak/uncertain topics, topics missed today, and the
   roadmap frontier (topics whose prerequisites are all ready).
2. If a target's prerequisites are not ready, practice the prerequisite instead.
3. Retrieve published questions for the targets and filter recent history.
4. Rank by six features, diversify by topic, log scores and reasons.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from .mastery import READY_ATTEMPTS, READY_MASTERY, is_ready, mastery_map
from .models import Attempt, Question, QuizSession, RecommendationLog, Topic, TopicEdge

ALGORITHM_VERSION = "graph-v1"
MAX_PER_TOPIC = 2
DIFFICULTY_LEVEL = {"Easy": 0, "Medium": 1, "Hard": 2}

WEIGHTS = {
    "weakness": 0.25,
    "missed_today": 0.25,
    "prerequisite_gap": 0.15,
    "novelty": 0.15,
    "difficulty_fit": 0.10,
    "staleness": 0.10,
}


@dataclass
class Target:
    reason: str
    missed_today: bool = False
    prerequisite_gap: bool = False
    priority: int = 0  # lower is more urgent


@dataclass
class Scored:
    question_id: int
    topic_id: str
    score: float
    reason: str
    features: dict[str, float] = field(default_factory=dict)


def _graph(db: Session) -> tuple[dict[str, Topic], dict[str, list[str]]]:
    topics = {t.id: t for t in db.scalars(select(Topic).order_by(Topic.position))}
    prereqs: dict[str, list[str]] = defaultdict(list)
    for e in db.scalars(select(TopicEdge)):
        prereqs[e.to_topic_id].append(e.from_topic_id)
    return topics, prereqs


def _target_level(mastery: float | None) -> int:
    if mastery is None or mastery < 0.5:
        return 0
    return 1 if mastery < 0.8 else 2


def recommend(
    db: Session,
    user_id: int,
    today: date,
    limit: int,
    purpose: str,  # "daily" (new material) or "extra" (react to today's performance)
    exclude: set[int] | None = None,
) -> list[Scored]:
    topics, prereqs = _graph(db)
    mastery = mastery_map(db, user_id)
    exclude = set(exclude or ())

    # Questions already served today in any session are not repeated.
    for qids in db.scalars(
        select(QuizSession.question_ids).where(
            QuizSession.user_id == user_id, QuizSession.local_date == today
        )
    ):
        exclude.update(qids)

    attempts = db.execute(
        select(Attempt.question_id, Attempt.is_correct, Attempt.local_date)
        .where(Attempt.user_id == user_id)
        .order_by(Attempt.created_at)
    ).all()
    last_seen: dict[int, date] = {}
    last_correct: dict[int, bool] = {}
    for qid, ok, d in attempts:
        last_seen[qid] = d
        last_correct[qid] = ok

    questions = list(
        db.scalars(
            select(Question)
            .where(Question.status == "published")
            .options(selectinload(Question.topics))
        )
    )
    missed_today_topics: set[str] = set()
    q_by_id = {q.id: q for q in questions}
    for qid, ok, d in attempts:
        if d == today and not ok and qid in q_by_id:
            missed_today_topics.update(t.topic_id for t in q_by_id[qid].topics)

    def unlocked(t: str) -> bool:
        return all(is_ready(mastery.get(p)) for p in prereqs.get(t, []))

    # --- 1-2. target topics, redirected to prerequisites when not ready
    targets: dict[str, Target] = {}

    def add_target(topic_id: str, target: Target) -> None:
        if topic_id not in targets or target.priority < targets[topic_id].priority:
            targets[topic_id] = target

    def aim_at(topic_id: str, reason: str, priority: int, missed: bool = False) -> None:
        if unlocked(topic_id):
            add_target(topic_id, Target(reason, missed_today=missed, priority=priority))
            return
        for p in prereqs.get(topic_id, []):
            if not is_ready(mastery.get(p)):
                add_target(
                    p,
                    Target(
                        f"Prerequisite for {topics[topic_id].name}",
                        missed_today=missed,
                        prerequisite_gap=True,
                        priority=priority,
                    ),
                )

    if purpose == "extra":
        for t in missed_today_topics:
            aim_at(t, "Missed today", 0, missed=True)
    for t, m in mastery.items():
        if m.mastery < READY_MASTERY:
            aim_at(t, f"Weak · {round(m.mastery * 100)}%", 1)
        elif m.attempts < READY_ATTEMPTS and unlocked(t):
            # Thin evidence on a locked topic (e.g. from a secondary tag) is not
            # a reason to jump ahead on the roadmap.
            aim_at(t, "Needs practice", 2)
    for t in topics:
        m = mastery.get(t)
        if unlocked(t) and (m is None or m.attempts < READY_ATTEMPTS):
            add_target(t, Target("Next on roadmap", priority=1 if purpose == "daily" else 3))

    # --- 3. retrieve and filter
    def eligible(q: Question, allow_seen: bool) -> bool:
        if q.id in exclude:
            return False
        if purpose == "daily" and not allow_seen and q.id in last_seen:
            return False
        # Recently answered correctly: leave it to the review schedule.
        if q.id in last_seen and last_correct.get(q.id) and (today - last_seen[q.id]).days < 3:
            return False
        return True

    def score(q: Question, target: Target | None, topic_id: str) -> Scored:
        m = mastery.get(topic_id)
        seen = q.id in last_seen
        features = {
            "weakness": 1 - (m.mastery if m else 0.5),
            "missed_today": 1.0 if target and target.missed_today else 0.0,
            "prerequisite_gap": 1.0 if target and target.prerequisite_gap else 0.0,
            "novelty": 1.0 if not seen else (0.3 if not last_correct.get(q.id) else 0.0),
            "difficulty_fit": 1 - abs(DIFFICULTY_LEVEL[q.difficulty] - _target_level(m.mastery if m else None)) / 2,
            "staleness": 1.0 if not seen else min((today - last_seen[q.id]).days, 30) / 30,
        }
        s = sum(WEIGHTS[k] * v for k, v in features.items())
        if target:
            s += 0.05 * (3 - target.priority)  # urgency tie-breaker
        # Stable roadmap order as the final tie-breaker.
        s -= topics[topic_id].position * 1e-4 + q.id * 1e-7
        reason = target.reason if target else "New topic"
        return Scored(q.id, topic_id, round(s, 6), reason, {k: round(v, 3) for k, v in features.items()})

    def ranked(allow_seen: bool, only_targets: bool) -> list[Scored]:
        out = []
        for q in questions:
            if not eligible(q, allow_seen):
                continue
            q_topics = [t.topic_id for t in q.topics]
            hit = next((t for t in q_topics if t in targets), None)
            if only_targets and hit is None:
                continue
            topic_id = hit or q_topics[0]
            out.append(score(q, targets.get(topic_id), topic_id))
        return sorted(out, key=lambda s: -s.score)

    # --- 4. diversify
    picked: list[Scored] = []
    per_topic: dict[str, int] = defaultdict(int)

    def take(candidates: list[Scored], cap: int | None) -> None:
        for c in candidates:
            if len(picked) >= limit:
                return
            if any(p.question_id == c.question_id for p in picked):
                continue
            if cap is not None and per_topic[c.topic_id] >= cap:
                continue
            picked.append(c)
            per_topic[c.topic_id] += 1

    take(ranked(allow_seen=False, only_targets=True), MAX_PER_TOPIC)
    take(ranked(allow_seen=False, only_targets=True), None)
    take(ranked(allow_seen=False, only_targets=False), None)
    if purpose == "daily":
        take(ranked(allow_seen=True, only_targets=False), None)

    db.add(
        RecommendationLog(
            user_id=user_id,
            algorithm_version=ALGORITHM_VERSION,
            items=[
                {"question_id": p.question_id, "topic": p.topic_id, "score": p.score,
                 "reason": p.reason, "features": p.features, "purpose": purpose}
                for p in picked
            ],
        )
    )
    return picked
