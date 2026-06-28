"""Root memory store — SQLite persistence of Lesson records + FTS5 recall."""

import re
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from qmem.store.scoring import score

DEFAULT_CONFIDENCE = 0.7


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _fts_query(query: str) -> str:
    """Turn user input into a safe FTS5 MATCH expression (OR-join tokens)."""
    terms = re.findall(r"[A-Za-z0-9_]+", query)
    return " OR ".join(f'"{t}"' for t in terms)


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
                stale         INTEGER NOT NULL DEFAULT 0,
                archived      INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        self._conn.execute(
            "CREATE VIRTUAL TABLE IF NOT EXISTS lessons_fts "
            "USING fts5(content, lesson_id UNINDEXED)"
        )
        self._conn.commit()

    # --- write -------------------------------------------------------------
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
            "archived": False,
        }
        self._conn.execute(
            """
            INSERT INTO lessons (
                id, trigger, wrong, "right", snippet, source, scope,
                confidence, use_count, success_count, fail_count,
                created_at, last_used, stale, archived
            ) VALUES (
                :id, :trigger, :wrong, :right, :snippet, :source, :scope,
                :confidence, :use_count, :success_count, :fail_count,
                :created_at, :last_used, :stale, :archived
            )
            """,
            {**lesson, "stale": int(lesson["stale"]), "archived": int(lesson["archived"])},
        )
        content = " ".join(
            filter(None, [lesson["trigger"], lesson["wrong"], lesson["right"], lesson["snippet"]])
        )
        self._conn.execute(
            "INSERT INTO lessons_fts (content, lesson_id) VALUES (?, ?)",
            (content, lesson["id"]),
        )
        self._conn.commit()
        return lesson

    def set_stale(self, lesson_id: str, stale: bool = True) -> None:
        self._conn.execute(
            "UPDATE lessons SET stale = ? WHERE id = ?", (int(stale), lesson_id)
        )
        self._conn.commit()

    def supersede(self, trigger: str) -> None:
        """Mark existing active lessons with the same trigger stale (new verification supersedes old)."""
        self._conn.execute(
            "UPDATE lessons SET stale = 1 WHERE trigger = ? AND stale = 0", (trigger,)
        )
        self._conn.commit()

    def set_archived(self, lesson_id: str, archived: bool = True) -> None:
        self._conn.execute(
            "UPDATE lessons SET archived = ? WHERE id = ?", (int(archived), lesson_id)
        )
        self._conn.commit()

    def apply_outcome(self, lesson_id: str, success: bool) -> dict | None:
        """Apply an outcome signal: bump success/fail counts and last_used."""
        col = "success_count" if success else "fail_count"
        self._conn.execute(
            f"UPDATE lessons SET {col} = {col} + 1, use_count = use_count + 1, "
            "last_used = ? WHERE id = ?",
            (_now(), lesson_id),
        )
        self._conn.commit()
        return self.get(lesson_id)

    # --- read --------------------------------------------------------------
    def _row_to_lesson(self, row: sqlite3.Row) -> dict:
        lesson = dict(row)
        lesson["stale"] = bool(lesson["stale"])
        lesson["archived"] = bool(lesson["archived"])
        return lesson

    def get(self, lesson_id: str) -> dict | None:
        row = self._conn.execute(
            "SELECT * FROM lessons WHERE id = ?", (lesson_id,)
        ).fetchone()
        return self._row_to_lesson(row) if row is not None else None

    def list_all(self) -> list[dict]:
        rows = self._conn.execute("SELECT * FROM lessons").fetchall()
        return [self._row_to_lesson(row) for row in rows]

    def recall(self, query: str, k: int = 10) -> list[dict]:
        match = _fts_query(query)
        if not match:
            return []
        rows = self._conn.execute(
            "SELECT lesson_id FROM lessons_fts WHERE content MATCH ?", (match,)
        ).fetchall()
        hits = []
        for r in rows:
            lesson = self.get(r["lesson_id"])
            if lesson and not lesson["stale"] and not lesson["archived"]:
                hits.append(lesson)
        hits.sort(key=score, reverse=True)
        return hits[:k]
