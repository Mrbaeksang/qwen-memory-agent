"""오프라인 데모 — `python demo/run_demo.py` (fake provider, 네트워크 0).

세션1에서 라이브러리 실수를 수확·검증해 Lesson을 만들고, 세션2(크로스세션)에서
자동 주입되는 것을 ON/OFF로 대비한다. confidence 막대로 자가 교정을 시각화한다.
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

    print("=== 세션 1 — 수확·검증된 Lesson ===")
    for lesson in result["created"]:
        print(f"  {lesson['trigger']}  →  {lesson['right']}")

    print("\n=== 세션 2 (크로스세션) — 메모리 ON vs OFF ===")
    print(f"  OFF: (주입 없음) → 같은 실수 반복 위험")
    print(f"  ON :\n{result['session2_on']}")

    lesson_id = result["created"][0]["id"]
    print("\n=== 자가 교정 — score 막대 (성공↑ / 실패↓) ===")
    print("초기:")
    print(render_score_bars(store.list_all()))
    for _ in range(3):
        apply_result(store, lesson_id, success=True)
    print("성공 3회 후:")
    print(render_score_bars(store.list_all()))
    for _ in range(5):
        apply_result(store, lesson_id, success=False)
    print("이후 실패 5회 후 (틀린 교훈 도태):")
    print(render_score_bars(store.list_all()))


if __name__ == "__main__":  # pragma: no cover
    main()
