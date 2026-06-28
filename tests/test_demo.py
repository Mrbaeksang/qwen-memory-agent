import json

from qmem.demo.scenario import run_scenario
from qmem.demo.viz import confidence_bar, render_confidence_bars, render_score_bars
from qmem.store.scoring import score
from qmem.llm.provider import FakeProvider
from qmem.store.memory import LessonStore


def test_confidence_bar_reflects_value():
    low = confidence_bar(0.1)
    high = confidence_bar(0.9)

    assert "0.10" in low and "0.90" in high
    assert high.count("█") > low.count("█")


def test_score_bar_rises_with_success():
    base = {"trigger": "x | t", "confidence": 0.7, "created_at": "2026-06-26T00:00:00+00:00",
            "last_used": "2026-06-26T00:00:00+00:00", "success_count": 0, "fail_count": 0}
    succeeded = {**base, "success_count": 5}

    assert score(succeeded) > score(base)
    assert render_score_bars([succeeded])  # renders


def test_render_confidence_bars_lists_each_lesson():
    out = render_confidence_bars(
        [{"trigger": "a | t", "confidence": 0.5}, {"trigger": "b | t", "confidence": 0.8}]
    )
    assert "a | t" in out and "b | t" in out
    assert out.count("\n") == 1


def test_scenario_session2_recalls_what_session1_learned(tmp_path):
    # installed-package fixture
    pkg = tmp_path / "node_modules" / "redis"
    pkg.mkdir(parents=True)
    (pkg / "package.json").write_text(json.dumps({"name": "redis", "version": "5.0.0"}))
    (pkg / "README.md").write_text("use redis.asyncio")
    # project manifest (the deps session 2 will read)
    (tmp_path / "package.json").write_text(json.dumps({"dependencies": {"redis": "^5"}}))

    store = LessonStore(tmp_path / "mem.db")
    provider = FakeProvider(
        by_model={
            "fake-extract": json.dumps(
                [{"tech": "redis", "wrong": "blocking client", "context": "async"}]
            ),
            "fake-chat": "Use redis.asyncio.Redis",
        }
    )

    result = run_scenario(
        store, provider, str(tmp_path), "used redis\nError: blocking call in async"
    )

    assert len(result["created"]) == 1
    assert "redis.asyncio" in result["session2_on"]   # ON: learned fix is injected
    assert result["session2_off"] == ""               # OFF: no injection
    assert result["session2_on"] != result["session2_off"]
