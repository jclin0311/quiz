# Pattern Quiz

A web app for learning to recognize algorithm patterns through short multiple-choice
quizzes: each question shows four approaches, you pick the best one, and a Socratic
explanation shows why each approach wins or loses. Built from `Design doc.docx`.

- **frontend/** — Next.js (App Router). Quiz UI, home, dashboard (Recharts), profile.
- **backend/** — FastAPI + SQLAlchemy (PostgreSQL or SQLite). Auth, quiz, review
  scheduling, mastery, graph-based recommendations, and the LLM analysis adapter.

The frontend proxies `/api/*` to the backend, so both are served from one origin and
the session cookie is first-party.

## Run locally

### First-time setup

```bash
cd backend
uv venv .venv && uv pip install -r requirements.txt --python .venv/bin/python
cd ../frontend
npm install
```

### Start

Use three terminal tabs, starting from the repo root.

```bash
# Tab 1 — database (Postgres in Docker)
docker compose up -d db

# Tab 2 — API at http://127.0.0.1:8000
cd backend
export DATABASE_URL=postgresql+psycopg://quiz:quiz@localhost:5432/quiz # optional, to skip docker, leave out tab 1 and the `DATABASE_URL` export. The API then uses a local SQLite file (`backend/quiz.db`).
export ANTHROPIC_API_KEY=...   # optional, enables the AI progress analysis
export GOOGLE_CLIENT_ID=...    # optional, enables Google sign-in
.venv/bin/uvicorn app.main:app --reload --port 8000

# Tab 3 — web app at http://localhost:3000
cd frontend
npm run dev
```

Open http://localhost:3000.

- Without `GOOGLE_CLIENT_ID`, the login page offers a demo account.
- On startup the API creates the tables and seeds the question bank, and it is safe to run every time.

### Stop

Press **Ctrl+C** in tabs 2 and 3, then stop the database:

```bash
docker compose stop      # keeps your data
docker compose down -v   # deletes the database too
```

If a server was started in the background, stop it with:

```bash
pkill -f "next (dev|start)"       # web app
pkill -f "uvicorn app.main:app"   # API
```

### Google sign-in

Create an OAuth 2.0 **Web** client in Google Cloud Console, add `http://localhost:3000`
as an authorized JavaScript origin, and set `GOOGLE_CLIENT_ID` on the backend. The
frontend reads the client id from `GET /api/auth/config`; the backend verifies the ID
token and issues its own httpOnly session cookie.

## Tests

```bash
cd backend && .venv/bin/python -m pytest -q
cd frontend && npx tsc --noEmit
```

## How it works

| Piece | Where | Notes |
|---|---|---|
| Plans | `plans.py` | Topic (roadmap, one pattern at a time), Random (no roadmap, one question per topic, tags hidden until answered), Sprint (Hot 100, then Top Interview 150). Chosen on the profile page. Each plan has its own Practice, Review and Extra; mastery and progress span all plans. |
| Daily practice | `recommend.py` (`purpose="daily"`) | `daily_goal` new questions, following the topic roadmap. The set is saved per local day. |
| Review | `scheduling.py` | A question first answered on day *d* is reviewed on *d*+1, 2, 6, 31. Missed days roll over. |
| Extra practice | `recommend.py` (`purpose="extra"`) | 5 questions targeting topics missed today. If a topic's prerequisites aren't ready, it practices the prerequisite first. |
| Mastery | `mastery.py` | Recency-weighted, smoothed accuracy per topic. A topic is "ready" at ≥ 65% over ≥ 3 answers. Recomputed when you leave or finish a quiz. |
| Grading | `routers/quiz.py` | Deterministic. The question payload never includes verdicts or explanations until an answer is recorded. Choice order is shuffled per session. |
| Analysis | `llm.py` | Only aggregate stats go to Claude (no email or ids). Any cited percentage must match a computed value, or it falls back to a template. Cached by stats hash. |

Topics and the roadmap follow the 12 topic lists from
[如何科学刷题](https://leetcode.cn/discuss/post/3141566/) (`backend/app/seed/topics.py`): the core
route is the spine, and each remaining list branches off the core topic it builds on.
Question content has original summaries and source links:

- `backend/app/seed/questions.py`: the 57-problem pilot bank, with company-tag provenance.
- `backend/app/seed/route/`: core-route problems rated ≤ 1700, one file per step, in route
  order (binary tree DFS and grid DFS so far).

On startup the seed keeps topics, edges and question tags in sync with these files and
rebuilds mastery if any tags moved.
