"""루트 메모리 저장소 — Lesson 레코드의 SQLite 영속화."""

import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_CONFIDENCE = 0.7


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class LessonStore:
    def __init__(self, db_path: Path):
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._create_schema()

    def _create_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS lessons (
                id            TEXT PRIMARY KEY,
                trigger       TEXT NOT NULL,
                wrong         TEXT,
                "right"       TEXT,
                snippet       TEXT,
                source        TEXT,
                scope         TEXT    NOT NULL DEFAULT 'global',
                confidence    REAL    NOT NULL DEFAULT 0.7,
                use_count     INTEGER NOT NULL DEFAULT 0,
                success_count INTEGER NOT NULL DEFAULT 0,
                fail_count    INTEGER NOT NULL DEFAULT 0,
                created_at    TEXT    NOT NULL,
                last_used     TEXT,
                stale         INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        self._conn.commit()

    def create(self, data: dict) -> dict:
        lesson = {
            "id": uuid.uuid4().hex,
            "trigger": data["trigger"],
            "wrong": data.get("wrong"),
            "right": data.get("right"),
            "snippet": data.get("snippet"),
            "source": data.get("source"),
            "scope": data.get("scope", "global"),
            "confidence": data.get("confidence", DEFAULT_CONFIDENCE),
            "use_count": 0,
            "success_count": 0,
            "fail_count": 0,
            "created_at": _now(),
            "last_used": None,
            "stale": False,
        }
        self._conn.execute(
            """
            INSERT INTO lessons (
                id, trigger, wrong, "right", snippet, source, scope,
                confidence, use_count, success_count, fail_count,
                created_at, last_used, stale
            ) VALUES (
                :id, :trigger, :wrong, :right, :snippet, :source, :scope,
                :confidence, :use_count, :success_count, :fail_count,
                :created_at, :last_used, :stale
            )
            """,
            {**lesson, "stale": int(lesson["stale"])},
        )
        self._conn.commit()
        return lesson

    def _row_to_lesson(self, row: sqlite3.Row) -> dict:
        lesson = dict(row)
        lesson["stale"] = bool(lesson["stale"])
        return lesson

    def get(self, lesson_id: str) -> dict | None:
        row = self._conn.execute(
            "SELECT * FROM lessons WHERE id = ?", (lesson_id,)
        ).fetchone()
        return self._row_to_lesson(row) if row is not None else None

    def list_all(self) -> list[dict]:
        rows = self._conn.execute("SELECT * FROM lessons").fetchall()
        return [self._row_to_lesson(row) for row in rows]
