from datetime import date

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from ..mastery import recompute_user_mastery
from ..models import (
    Attempt, Choice, Company, Question, QuestionCompany, QuestionTopic, Topic, TopicEdge, UserTopicMastery,
)
from .questions import LC, QUESTIONS
from .route import ROUTE_QUESTIONS
from .topics import EDGES, TOPICS

ALL_QUESTIONS = [*QUESTIONS, *ROUTE_QUESTIONS]

COMPANY = "Amazon"
TAG_PROVENANCE = "unverified"
TAG_OBSERVED = date(2026, 9, 28)


def validate_question(q: dict) -> None:
    choices = q["choices"]
    if len(choices) != 4:
        raise ValueError(f"{q['slug']}: expected 4 choices, got {len(choices)}")
    optimal = [c for c in choices if c[5] == "optimal"]
    if len(optimal) != 1:
        raise ValueError(f"{q['slug']}: expected exactly one optimal choice")
    if len({c[0] for c in choices}) != 4:
        raise ValueError(f"{q['slug']}: duplicate choice labels")


def seed(db: Session) -> None:
    """Idempotently load topics, the topic graph and the question bank.

    Topics, edges and question topic tags follow the seed, so retagging a
    question or retiring a topic here updates existing databases too.
    """
    existing_topics = {t.id: t for t in db.scalars(select(Topic))}
    for i, (tid, name, x, y) in enumerate(TOPICS):
        if tid in existing_topics:
            # Layout is presentation, not user data: keep it in sync with the seed.
            t = existing_topics[tid]
            t.name, t.position, t.x, t.y = name, i, x, y
        else:
            db.add(Topic(id=tid, name=name, position=i, x=x, y=y))
    wanted_edges = set(EDGES)
    existing_edges = set()
    for e in db.scalars(select(TopicEdge)):
        if (e.from_topic_id, e.to_topic_id) in wanted_edges:
            existing_edges.add((e.from_topic_id, e.to_topic_id))
        else:
            db.delete(e)
    for a, b in EDGES:
        if (a, b) not in existing_edges:
            db.add(TopicEdge(from_topic_id=a, to_topic_id=b))
    db.flush()

    company = db.scalar(select(Company).where(Company.name == COMPANY))
    if company is None:
        company = Company(name=COMPANY)
        db.add(company)
        db.flush()

    # Keep tag provenance text in sync with the seed.
    for qc in db.scalars(select(QuestionCompany).where(QuestionCompany.company_id == company.id)):
        qc.provenance = TAG_PROVENANCE

    pilot = {q["slug"] for q in QUESTIONS}
    existing = {q.slug: q for q in db.scalars(select(Question).options(selectinload(Question.topics)))}
    retagged = False
    for q in ALL_QUESTIONS:
        validate_question(q)
        source_url = q.get("url") or LC.format(q["slug"])
        if q["slug"] in existing:
            question = existing[q["slug"]]
            question.source_url, question.ref = source_url, q.get("ref")
            current = [t.topic_id for t in question.topics]
            if current[:1] != q["topics"][:1] or set(current) != set(q["topics"]):
                question.topics.clear()
                db.flush()
                question.topics = [
                    QuestionTopic(topic_id=t, is_primary=(i == 0)) for i, t in enumerate(q["topics"])
                ]
                retagged = True
            continue
        question = Question(
            slug=q["slug"],
            lc_number=q["n"],
            ref=q.get("ref"),
            title=q["title"],
            difficulty=q["diff"],
            summary=q["summary"],
            example=q["example"],
            criterion=q["criterion"],
            hint=q["hint"],
            source_url=source_url,
        )
        question.topics = [
            QuestionTopic(topic_id=t, is_primary=(i == 0)) for i, t in enumerate(q["topics"])
        ]
        question.choices = [
            Choice(
                position=i,
                label=c[0],
                detail=c[1],
                time_complexity=c[2],
                space_complexity=c[3],
                visual=c[4],
                verdict=c[5],
                explanation=c[6],
            )
            for i, c in enumerate(q["choices"])
        ]
        db.add(question)
        db.flush()
        if q["slug"] not in pilot:
            continue
        db.add(
            QuestionCompany(
                question_id=question.id,
                company_id=company.id,
                provenance=TAG_PROVENANCE,
                observed_on=TAG_OBSERVED,
            )
        )

    stale = set(existing_topics) - {t[0] for t in TOPICS}
    if stale:
        db.flush()
        db.execute(delete(UserTopicMastery).where(UserTopicMastery.topic_id.in_(stale)))
        db.execute(delete(QuestionTopic).where(QuestionTopic.topic_id.in_(stale)))
        db.execute(delete(Topic).where(Topic.id.in_(stale)))
    db.commit()

    # Mastery is per topic, so it is rebuilt from attempts whenever tags move.
    if retagged or stale:
        for user_id in db.scalars(select(Attempt.user_id).distinct()):
            recompute_user_mastery(db, user_id)
