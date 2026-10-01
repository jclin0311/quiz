from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..analytics import dashboard_stats
from ..auth import current_user
from ..clock import local_today
from ..db import get_db
from ..llm import performance_analysis
from ..mastery import mastery_map
from ..models import QuestionTopic, Topic, TopicEdge, User

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard")
def dashboard(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return dashboard_stats(db, user.id, local_today(user.timezone))


@router.get("/dashboard/analysis")
def analysis(user: User = Depends(current_user), db: Session = Depends(get_db)):
    stats = dashboard_stats(db, user.id, local_today(user.timezone))
    return performance_analysis(db, user.id, stats)


@router.get("/topics/graph")
def topic_graph(user: User = Depends(current_user), db: Session = Depends(get_db)):
    mastery = mastery_map(db, user.id)
    counts = {
        topic_id: n
        for topic_id, n in db.execute(
            select(QuestionTopic.topic_id, func.count())
            .where(QuestionTopic.is_primary.is_(True))
            .group_by(QuestionTopic.topic_id)
        )
    }
    nodes = []
    for t in db.scalars(select(Topic).order_by(Topic.position)):
        m = mastery.get(t.id)
        nodes.append(
            {
                "id": t.id,
                "name": t.name,
                "x": t.x,
                "y": t.y,
                "questions": counts.get(t.id, 0),
                "attempts": m.attempts if m else 0,
                "mastery": round(m.mastery * 100, 1) if m else None,
            }
        )
    edges = [{"from": e.from_topic_id, "to": e.to_topic_id} for e in db.scalars(select(TopicEdge))]
    return {"nodes": nodes, "edges": edges}
