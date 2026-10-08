import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .db import Base, SessionLocal, engine
from .migrate import migrate
from .routers import auth, dashboard, me, quiz
from .seed import seed

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    migrate(engine)
    with SessionLocal() as db:
        seed(db)
    yield


app = FastAPI(title="Pattern Quiz API", lifespan=lifespan)
app.include_router(auth.router)
app.include_router(me.router)
app.include_router(quiz.router)
app.include_router(dashboard.router)


@app.get("/api/health")
def health():
    return {"ok": True}
