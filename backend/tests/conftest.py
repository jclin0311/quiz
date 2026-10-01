import os
from datetime import datetime, timedelta, timezone

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["LLM_ENABLED"] = "false"
os.environ["ALLOW_DEV_LOGIN"] = "true"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import clock, db as db_module
from app.db import Base, get_db
from app.main import app
from app.seed import seed


class FakeClock:
    def __init__(self):
        self.value = datetime(2026, 9, 1, 15, 0, tzinfo=timezone.utc)

    def __call__(self):
        return self.value

    def advance(self, days=0, hours=0):
        self.value += timedelta(days=days, hours=hours)


@pytest.fixture
def fake_clock(monkeypatch):
    fc = FakeClock()
    monkeypatch.setattr(clock, "now", fc)
    return fc


@pytest.fixture
def client(fake_clock, monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    monkeypatch.setattr(db_module, "engine", engine)
    monkeypatch.setattr("app.main.engine", engine)
    monkeypatch.setattr("app.main.SessionLocal", Session)
    Base.metadata.create_all(engine)
    with Session() as s:
        seed(s)

    def override():
        s = Session()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = override
    with TestClient(app, headers={"X-Requested-With": "quiz"}) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def login(client):
    r = client.post("/api/auth/dev", json={"timezone": "UTC"})
    assert r.status_code == 200
    return client
