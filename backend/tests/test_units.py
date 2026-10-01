from datetime import date

from app.llm import fallback_narrative, validate_narrative
from app.mastery import compute_mastery
from app.seed import validate_question
from app.seed.questions import QUESTIONS
from app.seed.topics import EDGES, TOPICS


def test_seed_bank_is_well_formed():
    topic_ids = {t[0] for t in TOPICS}
    slugs = set()
    for q in QUESTIONS:
        validate_question(q)
        assert q["slug"] not in slugs
        slugs.add(q["slug"])
        assert set(q["topics"]) <= topic_ids
    assert len(QUESTIONS) >= 50
    for a, b in EDGES:
        assert a in topic_ids and b in topic_ids
    # every topic has at least two questions whose primary topic it is
    for tid in topic_ids:
        assert sum(q["topics"][0] == tid for q in QUESTIONS) >= 2, tid


def test_mastery_is_smoothed_and_recency_weighted():
    m1, c1 = compute_mastery([True])
    assert 0.5 < m1 < 0.7 and c1 < 0.2
    recent_good, _ = compute_mastery([True, True, True, False, False, False])
    recent_bad, _ = compute_mastery([False, False, False, True, True, True])
    assert recent_good > recent_bad


COMPACT = {
    "totals": {"answered": 10, "correct": 7, "accuracy": 70.0, "active_days": 2, "streak": 2,
               "this_week_answered": 10, "this_week_accuracy": 70.0, "last_week_answered": 0,
               "last_week_accuracy": None},
    "topic_accuracy_pct": [{"topic": "Stack", "attempts": 4, "accuracy_pct": 50.0},
                           {"topic": "Arrays & Hashing", "attempts": 6, "accuracy_pct": 83.3}],
    "mastery_pct": {"Stack": 50.0},
    "active_days_last_14": 2,
    "answered_last_14_days": 10,
}


def test_narrative_validation_rejects_invented_numbers():
    assert validate_narrative("You're at 70% overall; Stack is 50%.", COMPACT)
    assert validate_narrative("Arrays sits at 83.3%.", COMPACT)
    assert not validate_narrative("You improved to 95% this week.", COMPACT)
    assert not validate_narrative("", COMPACT)


def test_fallback_narrative_passes_its_own_validation():
    text = fallback_narrative(COMPACT)
    assert "Stack" in text and validate_narrative(text, COMPACT)
    assert text.count(".") <= 2
