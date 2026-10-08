from datetime import date, datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    google_sub: Mapped[str | None] = mapped_column(String(255), unique=True)
    email: Mapped[str | None] = mapped_column(String(320))
    name: Mapped[str] = mapped_column(String(200), default="")
    avatar_url: Mapped[str | None] = mapped_column(String(1000))
    display_name: Mapped[str] = mapped_column(String(80), default="")
    timezone: Mapped[str] = mapped_column(String(64), default="UTC")
    daily_goal: Mapped[int] = mapped_column(Integer, default=5)
    plan: Mapped[str] = mapped_column(String(10), default="topic")  # see plans.py
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AuthSession(Base):
    __tablename__ = "auth_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    position: Mapped[int] = mapped_column(Integer, default=0)
    # Layout coordinates for the roadmap graph (0-100 grid units).
    x: Mapped[float] = mapped_column(Float, default=0)
    y: Mapped[float] = mapped_column(Float, default=0)


class TopicEdge(Base):
    """from_topic is a prerequisite of to_topic."""

    __tablename__ = "topic_edges"

    from_topic_id: Mapped[str] = mapped_column(ForeignKey("topics.id"), primary_key=True)
    to_topic_id: Mapped[str] = mapped_column(ForeignKey("topics.id"), primary_key=True)


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(120))
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(20), default="published")
    lc_number: Mapped[int | None] = mapped_column(Integer)
    # Display id for problems without a LeetCode number, e.g. "LCP 67" (leetcode.cn only).
    ref: Mapped[str | None] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(200))
    difficulty: Mapped[str] = mapped_column(String(10))
    # Original summary, not the source problem text.
    summary: Mapped[str] = mapped_column(Text)
    example: Mapped[str] = mapped_column(Text, default="")
    criterion: Mapped[str] = mapped_column(Text)
    hint: Mapped[str] = mapped_column(Text, default="")
    source_url: Mapped[str] = mapped_column(String(500), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    topics: Mapped[list["QuestionTopic"]] = relationship(
        cascade="all, delete-orphan", order_by="QuestionTopic.is_primary.desc()"
    )
    choices: Mapped[list["Choice"]] = relationship(
        cascade="all, delete-orphan", order_by="Choice.position"
    )

    __table_args__ = (UniqueConstraint("slug", "version"),)

    @property
    def primary_topic_id(self) -> str:
        return self.topics[0].topic_id


class QuestionTopic(Base):
    __tablename__ = "question_topics"

    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"), primary_key=True
    )
    topic_id: Mapped[str] = mapped_column(ForeignKey("topics.id"), primary_key=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)


class QuestionCompany(Base):
    __tablename__ = "question_companies"

    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"), primary_key=True
    )
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), primary_key=True)
    provenance: Mapped[str] = mapped_column(String(200), default="")
    observed_on: Mapped[date | None] = mapped_column(Date)


class Choice(Base):
    __tablename__ = "choices"

    id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"), index=True
    )
    position: Mapped[int] = mapped_column(Integer)
    label: Mapped[str] = mapped_column(String(120))
    detail: Mapped[str] = mapped_column(Text)
    time_complexity: Mapped[str] = mapped_column(String(40))
    space_complexity: Mapped[str] = mapped_column(String(40))
    visual: Mapped[str] = mapped_column(String(40))
    # optimal | suboptimal (valid but not best) | incorrect
    verdict: Mapped[str] = mapped_column(String(20))
    explanation: Mapped[str] = mapped_column(Text)


class QuizSession(Base):
    __tablename__ = "quiz_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    mode: Mapped[str] = mapped_column(String(10))  # daily | review | extra
    plan: Mapped[str] = mapped_column(String(10), default="topic")
    local_date: Mapped[date] = mapped_column(Date, index=True)
    question_ids: Mapped[list[int]] = mapped_column(JSON)
    # question_id (as str) -> shuffled list of choice ids
    choice_orders: Mapped[dict[str, list[int]]] = mapped_column(JSON)
    reasons: Mapped[dict[str, str]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Attempt(Base):
    __tablename__ = "attempts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("quiz_sessions.id", ondelete="CASCADE"))
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"))
    choice_id: Mapped[int] = mapped_column(ForeignKey("choices.id"))
    is_correct: Mapped[bool] = mapped_column(Boolean)
    mode: Mapped[str] = mapped_column(String(10))
    plan: Mapped[str] = mapped_column(String(10), default="topic")
    local_date: Mapped[date] = mapped_column(Date, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    __table_args__ = (UniqueConstraint("session_id", "question_id"),)


class ReviewItem(Base):
    """One scheduled review of a question, created when it is first solved in a plan."""

    __tablename__ = "review_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    plan: Mapped[str] = mapped_column(String(10), default="topic")
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"))
    stage: Mapped[int] = mapped_column(Integer)
    due_date: Mapped[date] = mapped_column(Date, index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        UniqueConstraint("user_id", "plan", "question_id", "stage", name="uq_review_items_user_plan_question_stage"),
    )


class UserTopicMastery(Base):
    __tablename__ = "user_topic_mastery"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    topic_id: Mapped[str] = mapped_column(ForeignKey("topics.id"), primary_key=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    correct: Mapped[int] = mapped_column(Integer, default=0)
    mastery: Mapped[float] = mapped_column(Float, default=0)
    confidence: Mapped[float] = mapped_column(Float, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class RecommendationLog(Base):
    __tablename__ = "recommendation_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    algorithm_version: Mapped[str] = mapped_column(String(20))
    items: Mapped[list[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AnalysisReport(Base):
    __tablename__ = "analysis_reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    stats_hash: Mapped[str] = mapped_column(String(64))
    text: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(20))  # llm | fallback
    model: Mapped[str | None] = mapped_column(String(64))
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    input_tokens: Mapped[int | None] = mapped_column(Integer)
    output_tokens: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
