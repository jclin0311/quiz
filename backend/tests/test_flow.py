def answer_items(client, session, correct: bool):
    """Answer each item correctly or incorrectly using the answer key from a probe."""
    from app.models import Choice
    from app.db import get_db
    from app.main import app

    gen = app.dependency_overrides[get_db]()
    db = next(gen)
    for item in session["items"]:
        qid = item["question"]["id"]
        choices = {c.id: c.verdict for c in db.query(Choice).filter(Choice.question_id == qid)}
        pick = next(cid for cid, v in choices.items() if (v == "optimal") == correct)
        r = client.post(f"/api/sessions/{session['id']}/answer", json={"question_id": qid, "choice_id": pick})
        assert r.status_code == 200
        assert r.json()["is_correct"] is correct
    return client.post(f"/api/sessions/{session['id']}/finish").json()


def test_requires_login_and_csrf_header(client):
    assert client.get("/api/me").status_code == 401
    r = client.post("/api/auth/dev", json={}, headers={"X-Requested-With": ""})
    assert r.status_code == 403


def test_payload_hides_answers_until_answered(login):
    s = login.post("/api/sessions", json={"mode": "daily"}).json()
    item = s["items"][0]
    assert item["result"] is None
    assert all("verdict" not in c and "explanation" not in c for c in item["choices"])
    assert len(item["choices"]) == 4


def test_daily_set_is_saved_and_starts_at_roadmap_root(login):
    a = login.post("/api/sessions", json={"mode": "daily"}).json()
    b = login.post("/api/sessions", json={"mode": "daily"}).json()
    assert a["id"] == b["id"]
    assert len(a["items"]) == 5
    assert all(i["question"]["topics"][0]["id"] == "sliding-window" for i in a["items"])


def test_answer_is_idempotent(login):
    s = login.post("/api/sessions", json={"mode": "daily"}).json()
    item = s["items"][0]
    qid = item["question"]["id"]
    first = login.post(f"/api/sessions/{s['id']}/answer", json={"question_id": qid, "choice_id": item["choices"][0]["id"]}).json()
    second = login.post(f"/api/sessions/{s['id']}/answer", json={"question_id": qid, "choice_id": item["choices"][1]["id"]}).json()
    assert first == second


def test_review_schedule_follows_forgetting_curve(login, fake_clock):
    daily = login.post("/api/sessions", json={"mode": "daily"}).json()
    qids = {i["question"]["id"] for i in daily["items"]}
    answer_items(login, daily, correct=True)
    assert login.post("/api/sessions", json={"mode": "review"}).status_code == 409  # nothing due day 0

    due_days = []
    for day in range(1, 35):
        fake_clock.advance(days=1)
        login.post("/api/auth/dev", json={})  # sessions expire after 30 days
        r = login.post("/api/sessions", json={"mode": "review"})
        assert r.status_code in (200, 409)
        if r.status_code == 200:
            review = r.json()
            assert {i["question"]["id"] for i in review["items"]} == qids
            answer_items(login, review, correct=True)
            due_days.append(day)
    assert due_days == [1, 2, 6, 31]


def test_missed_reviews_roll_over(login, fake_clock):
    daily = login.post("/api/sessions", json={"mode": "daily"}).json()
    answer_items(login, daily, correct=True)
    fake_clock.advance(days=3)  # skipped days 1 and 2
    review = login.post("/api/sessions", json={"mode": "review"}).json()
    assert len(review["items"]) == 5
    answer_items(login, review, correct=True)
    fake_clock.advance(days=1)  # day 4: nothing due until day 6
    assert login.post("/api/sessions", json={"mode": "review"}).status_code == 409


def test_mastery_unlocks_next_topics(login, fake_clock):
    daily = login.post("/api/sessions", json={"mode": "daily"}).json()
    answer_items(login, daily, correct=True)
    fake_clock.advance(days=1)
    nxt = login.post("/api/sessions", json={"mode": "daily"}).json()
    topics = {i["question"]["topics"][0]["id"] for i in nxt["items"]}
    assert topics & {"binary-search", "bit-manipulation"}
    assert "trees" not in topics


def test_extra_practice_targets_today_misses(login):
    daily = login.post("/api/sessions", json={"mode": "daily"}).json()
    answer_items(login, daily, correct=False)
    extra = login.post("/api/sessions", json={"mode": "extra"}).json()
    daily_ids = {i["question"]["id"] for i in daily["items"]}
    assert len(extra["items"]) == 5
    assert not daily_ids & {i["question"]["id"] for i in extra["items"]}


def test_home_and_dashboard(login):
    home = login.get("/api/home").json()
    assert home["streak"] == 0 and home["daily"]["session_id"] is None
    daily = login.post("/api/sessions", json={"mode": "daily"}).json()
    answer_items(login, daily, correct=True)
    home = login.get("/api/home").json()
    assert home["streak"] == 1 and home["daily"]["answered"] == 5
    dash = login.get("/api/dashboard").json()
    assert dash["totals"]["answered"] == 5 and dash["totals"]["accuracy"] == 100.0
    assert dash["topic_accuracy"][0]["topic"] == "sliding-window"
    assert dash["per_day"][-1]["answered"] == 5
    analysis = login.get("/api/dashboard/analysis").json()
    assert analysis["source"] == "fallback" and "5 questions" in analysis["text"]
    graph = login.get("/api/topics/graph").json()
    root = next(n for n in graph["nodes"] if n["id"] == "sliding-window")
    assert root["mastery"] is not None and len(graph["nodes"]) == 12 and len(graph["edges"]) == 11


def test_profile_update_validation(login):
    assert login.patch("/api/me", json={"daily_goal": 50}).status_code == 422
    assert login.patch("/api/me", json={"timezone": "Mars/Base"}).status_code == 422
    me = login.patch("/api/me", json={"display_name": "Ada", "daily_goal": 3, "timezone": "Asia/Shanghai"}).json()
    assert me["display_name"] == "Ada" and me["daily_goal"] == 3
    assert len(login.post("/api/sessions", json={"mode": "daily"}).json()["items"]) == 3


def test_cannot_access_other_users_session(login, client):
    s = login.post("/api/sessions", json={"mode": "daily"}).json()
    client.post("/api/auth/logout")
    assert client.get(f"/api/sessions/{s['id']}").status_code == 401


def test_plans_keep_separate_sets_and_reviews(login, fake_clock):
    topic = login.post("/api/sessions", json={"mode": "daily"}).json()
    assert topic["plan"] == "topic"
    answer_items(login, topic, correct=True)

    assert login.patch("/api/me", json={"plan": "bogus"}).status_code == 422
    assert login.patch("/api/me", json={"plan": "random"}).json()["plan"] == "random"
    home = login.get("/api/home").json()
    assert home["daily"]["session_id"] is None and home["daily"]["answered"] == 0
    rand = login.post("/api/sessions", json={"mode": "daily"}).json()
    assert rand["id"] != topic["id"] and rand["plan"] == "random" and rand["hide_topics"]

    fake_clock.advance(days=1)
    login.post("/api/auth/dev", json={})
    # Reviews due tomorrow belong to the plan they were solved in.
    assert login.post("/api/sessions", json={"mode": "review"}).status_code == 409
    login.patch("/api/me", json={"plan": "topic"})
    review = login.post("/api/sessions", json={"mode": "review"}).json()
    assert {i["question"]["id"] for i in review["items"]} == {i["question"]["id"] for i in topic["items"]}

    # Progress spans every plan.
    assert login.get("/api/dashboard").json()["totals"]["answered"] == 5


def test_random_plan_ignores_roadmap(login):
    login.patch("/api/me", json={"plan": "random"})
    s = login.post("/api/sessions", json={"mode": "daily"}).json()
    topics = [i["question"]["topics"][0]["id"] for i in s["items"]]
    assert len(set(topics)) == len(topics) == 5  # one per topic
    assert set(topics) != {"sliding-window"}


def test_sprint_plan_draws_from_interview_lists(login):
    from app.plans import HOT_100, TOP_INTERVIEW_150

    login.patch("/api/me", json={"plan": "sprint", "daily_goal": 20})
    s = login.post("/api/sessions", json={"mode": "daily"}).json()
    numbers = [i["question"]["lc_number"] for i in s["items"]]
    assert all(n in HOT_100 | TOP_INTERVIEW_150 for n in numbers)
    assert all(n in HOT_100 for n in numbers[:10])
    assert {i["reason"] for i in s["items"]} <= {"Hot 100", "Interview 150"}


def test_mastery_from_one_plan_steers_another(login):
    daily = login.post("/api/sessions", json={"mode": "daily"}).json()
    answer_items(login, daily, correct=False)  # weak on sliding window, learned in topic plan
    login.patch("/api/me", json={"plan": "sprint"})
    extra = login.post("/api/sessions", json={"mode": "extra"}).json()
    assert extra["items"][0]["question"]["topics"][0]["id"] == "sliding-window"
    assert extra["items"][0]["reason"] == "Missed today"


def test_abandoned_extra_is_reopened_and_counts_only_answers(login):
    first = login.post("/api/sessions", json={"mode": "extra"}).json()
    login.post(f"/api/sessions/{first['id']}/finish")  # leave without answering
    again = login.post("/api/sessions", json={"mode": "extra"}).json()
    assert again["id"] == first["id"]
    assert [p["answered"] for p in login.get("/api/home").json()["extra"]] == [0]

    answer_items(login, again, correct=True)
    nxt = login.post("/api/sessions", json={"mode": "extra"}).json()
    assert nxt["id"] != first["id"]
    assert sum(p["answered"] for p in login.get("/api/home").json()["extra"]) == 5


def test_leetcode_cn_question_links_to_cn(login):
    from app.models import Question

    from app.db import get_db
    from app.main import app

    db = next(app.dependency_overrides[get_db]())
    q = db.query(Question).filter(Question.slug == "lcp-67-decorate-tree").one()
    assert q.lc_number is None and q.ref == "LCP 67" and q.source_url.startswith("https://leetcode.cn/")
