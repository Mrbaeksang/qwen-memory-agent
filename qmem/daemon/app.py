"""데몬 HTTP API (Seam 1) — Lesson 저장/조회 경계."""

from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, HTTPException
from pydantic import BaseModel

from qmem.daemon.harvest import harvest, read_transcript
from qmem.daemon.inject import build_context, recall_for_deps
from qmem.daemon.manifest import read_dependencies
from qmem.llm.provider import QwenProvider
from qmem.store.memory import LessonStore
from qmem.verify.verifier import verify_and_store


class LessonIn(BaseModel):
    trigger: str
    wrong: str | None = None
    right: str | None = None
    snippet: str | None = None
    source: str | None = None
    scope: str = "global"
    confidence: float = 0.7


def create_app(db_path: str | Path, provider=None) -> FastAPI:
    app = FastAPI()
    store = LessonStore(Path(db_path))
    provider = provider or QwenProvider()
    # 세션당 1회 주입 보증: session_id -> 이미 주입한 lesson_id 집합
    injected: dict[str, set[str]] = {}
    # PreCompact가 수확한 미검증 후보 (S8 Verify가 소비)
    pending: list[dict] = []

    def _harvest_job(transcript_path: str | None, cwd: str | None) -> None:
        candidates = harvest(read_transcript(transcript_path), provider)
        pending.extend(candidates)
        verify_and_store(candidates, [cwd or "."], provider, store)

    @app.post("/lessons", status_code=201)
    def create_lesson(lesson: LessonIn) -> dict:
        return store.create(lesson.model_dump())

    @app.get("/lessons")
    def list_lessons() -> list[dict]:
        return store.list_all()

    @app.get("/recall")
    def recall(q: str, k: int = 10) -> list[dict]:
        return store.recall(q, k)

    @app.get("/pending")
    def get_pending() -> list[dict]:
        return pending

    @app.post("/events")
    def events(event: dict, background_tasks: BackgroundTasks) -> dict:
        name = event.get("event")
        if name == "PreCompact":
            # 비동기로 처리해 호스트 응답을 막지 않음
            background_tasks.add_task(
                _harvest_job, event.get("transcript_path"), event.get("cwd")
            )
            return {}
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
