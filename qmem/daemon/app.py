"""데몬 HTTP API (Seam 1) — Lesson 저장/조회 경계."""

from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from qmem.daemon.inject import build_context, recall_for_deps
from qmem.daemon.manifest import read_dependencies
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
    # 세션당 1회 주입 보증: session_id -> 이미 주입한 lesson_id 집합
    injected: dict[str, set[str]] = {}

    @app.post("/lessons", status_code=201)
    def create_lesson(lesson: LessonIn) -> dict:
        return store.create(lesson.model_dump())

    @app.get("/lessons")
    def list_lessons() -> list[dict]:
        return store.list_all()

    @app.get("/recall")
    def recall(q: str, k: int = 10) -> list[dict]:
        return store.recall(q, k)

    @app.post("/events")
    def events(event: dict) -> dict:
        name = event.get("event")
        if name == "SessionStart":
            deps = read_dependencies(event.get("cwd") or ".")
            lessons = recall_for_deps(store, deps)
            context = build_context(lessons)
            return {"context": context or None}
        if name == "UserPromptSubmit":
            sid = event.get("session_id") or ""
            lessons = store.recall(event.get("prompt") or "")
            already = injected.setdefault(sid, set())
            fresh = [lesson for lesson in lessons if lesson["id"] not in already]
            for lesson in fresh:
                already.add(lesson["id"])
            context = build_context(fresh)
            return {"context": context or None}
        if name == "SessionEnd":
            injected.pop(event.get("session_id") or "", None)
            return {}
        return {}

    @app.get("/lessons/{lesson_id}")
    def get_lesson(lesson_id: str) -> dict:
        lesson = store.get(lesson_id)
        if lesson is None:
            raise HTTPException(status_code=404, detail="lesson not found")
        return lesson

    return app
