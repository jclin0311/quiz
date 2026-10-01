from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Choice, Company, Question, QuestionCompany, QuestionTopic, Topic, TopicEdge
from .questions import LC, QUESTIONS
from .topics import EDGES, TOPICS

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
    """Idempotently load topics, the topic graph and the pilot question bank."""
    existing_topics = {t.id: t for t in db.scalars(select(Topic))}
    for i, (tid, name, x, y) in enumerate(TOPICS):
        if tid in existing_topics:
            # Layout is presentation, not user data: keep it in sync with the seed.
            t = existing_topics[tid]
            t.name, t.position, t.x, t.y = name, i, x, y
        else:
            db.add(Topic(id=tid, name=name, position=i, x=x, y=y))
    existing_edges = {(a, b) for a, b in db.execute(select(TopicEdge.from_topic_id, TopicEdge.to_topic_id))}
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

    existing = set(db.scalars(select(Question.slug)))
    for q in QUESTIONS:
        validate_question(q)
        if q["slug"] in existing:
            continue
        question = Question(
            slug=q["slug"],
            lc_number=q["n"],
            title=q["title"],
            difficulty=q["diff"],
            summary=q["summary"],
            example=q["example"],
            criterion=q["criterion"],
            hint=q["hint"],
            source_url=LC.format(q["slug"]),
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
        db.add(
            QuestionCompany(
                question_id=question.id,
                company_id=company.id,
                provenance=TAG_PROVENANCE,
                observed_on=TAG_OBSERVED,
            )
        )
    db.commit()
