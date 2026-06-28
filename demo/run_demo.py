"""Offline demo — `python demo/run_demo.py` (fake provider, zero network).

Session 1 harvests + verifies a library mistake into a Lesson; session 2 (cross-session)
shows it auto-injected, contrasted ON vs OFF. Score bars visualize self-correction.
"""

import json
import tempfile
from pathlib import Path

from qmem.daemon.reflect import apply_result
from qmem.demo.scenario import run_scenario
from qmem.demo.viz import render_score_bars
from qmem.llm.provider import FakeProvider
from qmem.store.memory import LessonStore


def main() -> None:
    tmp = Path(tempfile.mkdtemp())
    pkg = tmp / "node_modules" / "redis"
    pkg.mkdir(parents=True)
    (pkg / "package.json").write_text(json.dumps({"name": "redis", "version": "5.0.0"}))
    (pkg / "README.md").write_text("use redis.asyncio for async clients")
    (tmp / "package.json").write_text(json.dumps({"dependencies": {"redis": "^5"}}))

    store = LessonStore(tmp / "mem.db")
    provider = FakeProvider(
        by_model={
            "fake-extract": json.dumps(
                [{"tech": "redis", "wrong": "blocking client", "context": "async"}]
            ),
            "fake-chat": "Use redis.asyncio.Redis for async clients",
        }
    )

    result = run_scenario(store, provider, str(tmp), "used redis\nError: blocking call in async")

    print("=== Session 1 — harvested & verified Lesson ===")
    for lesson in result["created"]:
        print(f"  {lesson['trigger']}  ->  {lesson['right']}")

    print("\n=== Session 2 (cross-session) — memory ON vs OFF ===")
    print("  OFF: (no injection) -> risk of repeating the same mistake")
    print(f"  ON :\n{result['session2_on']}")

    lesson_id = result["created"][0]["id"]
    print("\n=== Self-correction — score bars (success↑ / fail↓) ===")
    print("initial:")
    print(render_score_bars(store.list_all()))
    for _ in range(3):
        apply_result(store, lesson_id, success=True)
    print("after 3 successes:")
    print(render_score_bars(store.list_all()))
    for _ in range(5):
        apply_result(store, lesson_id, success=False)
    print("then after 5 failures (wrong lesson demoted):")
    print(render_score_bars(store.list_all()))


if __name__ == "__main__":  # pragma: no cover
    main()
