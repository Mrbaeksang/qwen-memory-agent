"""데몬 HTTP API (Seam 1) — Lesson 저장/조회 경계."""

from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from qmem.store.memory import LessonStore


class LessonIn(BaseModel):
    trigger: str
    wrong: str | None = None
    right: str | None = None
    snippet: str | None = None
    source: str | None = None
    scope: str = "global"
    confidence: float = 0.7


def create_app(db_path: str | Path) -> FastAPI:
    app = FastAPI()
    store = LessonStore(Path(db_path))

    @app.post("/lessons", status_code=201)
    def create_lesson(lesson: LessonIn) -> dict:
        return store.create(lesson.model_dump())

    @app.get("/lessons")
    def list_lessons() -> list[dict]:
        return store.list_all()

    @app.get("/recall")
    def recall(q: str, k: int = 10) -> list[dict]:
        return store.recall(q, k)

    @app.get("/lessons/{lesson_id}")
    def get_lesson(lesson_id: str) -> dict:
        lesson = store.get(lesson_id)
        if lesson is None:
            raise HTTPException(status_code=404, detail="lesson not found")
        return lesson

    return app
