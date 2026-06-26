import pytest

from qmem.store.memory import LessonStore


@pytest.fixture
def store(tmp_path):
    return LessonStore(tmp_path / "recall.db")


def test_recall_matches_indexed_content(store):
    store.create({"trigger": "sqlalchemy==2.0 | async", "wrong": "sync Session"})
    store.create({"trigger": "redis-py | pubsub", "wrong": "blocking client"})

    hits = store.recall("sqlalchemy")

    assert [h["trigger"] for h in hits] == ["sqlalchemy==2.0 | async"]


def test_recall_orders_by_score_confidence(store):
    store.create({"trigger": "fastapi | deps", "snippet": "low", "confidence": 0.3})
    store.create({"trigger": "fastapi | deps", "snippet": "high", "confidence": 0.9})

    hits = store.recall("fastapi")

    assert [h["snippet"] for h in hits] == ["high", "low"]


def test_recall_excludes_stale(store):
    keep = store.create({"trigger": "numpy | dtype", "snippet": "keep"})
    drop = store.create({"trigger": "numpy | dtype", "snippet": "drop"})
    store.set_stale(drop["id"])

    hits = store.recall("numpy")

    assert [h["snippet"] for h in hits] == ["keep"]


async def test_recall_endpoint_returns_matches(client):
    await client.post("/lessons", json={"trigger": "pytest | fixtures", "wrong": "x"})

    resp = await client.get("/recall", params={"q": "pytest"})

    assert resp.status_code == 200
    assert [h["trigger"] for h in resp.json()] == ["pytest | fixtures"]
