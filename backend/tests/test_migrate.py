from sqlalchemy import create_engine, inspect, text

from app.db import Base
from app.migrate import migrate

OLD_REVIEW_ITEMS = """
CREATE TABLE review_items (
    id INTEGER PRIMARY KEY, user_id INTEGER, question_id INTEGER, stage INTEGER,
    due_date DATE, completed_at DATETIME, UNIQUE (user_id, question_id, stage)
)"""


def test_migrate_upgrades_pre_plan_schema(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'old.db'}")
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY, name VARCHAR)"))
        conn.execute(text("CREATE TABLE quiz_sessions (id INTEGER PRIMARY KEY, mode VARCHAR)"))
        conn.execute(text("CREATE TABLE attempts (id INTEGER PRIMARY KEY, mode VARCHAR)"))
        conn.execute(text(OLD_REVIEW_ITEMS))
        conn.execute(text("CREATE INDEX ix_review_items_user_id ON review_items (user_id)"))
        conn.execute(text("INSERT INTO review_items VALUES (1, 1, 7, 0, '2026-09-02', NULL)"))
    Base.metadata.create_all(engine)  # creates the other tables, leaves these alone
    migrate(engine)
    migrate(engine)  # idempotent

    insp = inspect(engine)
    for table in ("users", "quiz_sessions", "attempts", "review_items"):
        assert "plan" in {c["name"] for c in insp.get_columns(table)}
    assert [u["column_names"] for u in insp.get_unique_constraints("review_items")] == [
        ["user_id", "plan", "question_id", "stage"]
    ]
    with engine.begin() as conn:
        assert conn.execute(text("SELECT plan, question_id FROM review_items")).all() == [("topic", 7)]
        # The same question can now be scheduled in another plan.
        conn.execute(text("INSERT INTO review_items (user_id, plan, question_id, stage, due_date) "
                          "VALUES (1, 'sprint', 7, 0, '2026-09-02')"))


def test_seed_retags_existing_bank_and_retires_old_topics():
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    from app.models import Attempt, Question, QuestionTopic, QuizSession, Topic, TopicEdge, User, UserTopicMastery
    from app.seed import seed

    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    seed(db)
    # Simulate the old roadmap: an "arrays" topic with an edge, a retagged question and mastery on it.
    db.add(Topic(id="arrays", name="Arrays & Hashing"))
    db.flush()
    db.add(TopicEdge(from_topic_id="arrays", to_topic_id="sliding-window"))
    two_sum = db.scalar(select_q(Question, "two-sum"))
    two_sum.topics.clear()
    db.flush()
    two_sum.topics = [QuestionTopic(topic_id="arrays", is_primary=True)]
    user = User(name="a")
    db.add(user)
    db.flush()
    s = QuizSession(user_id=user.id, mode="daily", local_date=__import__("datetime").date(2026, 9, 1),
                    question_ids=[two_sum.id], choice_orders={})
    db.add(s)
    db.flush()
    db.add(Attempt(user_id=user.id, session_id=s.id, question_id=two_sum.id, choice_id=two_sum.choices[0].id,
                   is_correct=True, mode="daily", local_date=s.local_date))
    db.add(UserTopicMastery(user_id=user.id, topic_id="arrays", attempts=1, correct=1, mastery=0.6, confidence=0.1))
    db.commit()

    seed(db)
    assert db.get(Topic, "arrays") is None
    assert [t.topic_id for t in db.scalar(select_q(Question, "two-sum")).topics] == ["data-structures"]
    assert {m.topic_id for m in db.query(UserTopicMastery)} == {"data-structures"}
    assert db.query(TopicEdge).count() == 11


def select_q(model, slug):
    from sqlalchemy import select

    return select(model).where(model.slug == slug)
