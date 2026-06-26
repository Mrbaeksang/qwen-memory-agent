async def test_post_lesson_stores_and_fills_defaults(client):
    payload = {
        "trigger": "sqlalchemy==2.0.31 | async test",
        "wrong": "sync Session with asyncpg",
        "right": "AsyncSession + savepoint rollback fixture",
    }

    resp = await client.post("/lessons", json=payload)

    assert resp.status_code == 201
    body = resp.json()
    assert body["id"]
    assert body["trigger"] == payload["trigger"]
    assert body["wrong"] == payload["wrong"]
    assert body["right"] == payload["right"]
    # 기본값이 채워진다
    assert body["confidence"] == 0.7
    assert body["use_count"] == 0
    assert body["success_count"] == 0
    assert body["fail_count"] == 0
    assert body["stale"] is False
    assert body["created_at"]


async def test_get_lesson_returns_stored_record(client):
    created = (
        await client.post(
            "/lessons",
            json={"trigger": "redis-py | async pubsub", "right": "use redis.asyncio"},
        )
    ).json()

    resp = await client.get(f"/lessons/{created['id']}")

    assert resp.status_code == 200
    assert resp.json() == created


async def test_get_missing_lesson_returns_404(client):
    resp = await client.get("/lessons/does-not-exist")

    assert resp.status_code == 404


async def test_list_lessons_returns_all_stored(client):
    await client.post("/lessons", json={"trigger": "pkg-a | task"})
    await client.post("/lessons", json={"trigger": "pkg-b | task"})

    resp = await client.get("/lessons")

    assert resp.status_code == 200
    triggers = {lesson["trigger"] for lesson in resp.json()}
    assert triggers == {"pkg-a | task", "pkg-b | task"}


async def test_post_without_required_trigger_is_rejected(client):
    # trigger 누락 — 검증 단계에서 막혀야 하고 서버가 죽지 않는다(fail-safe)
    resp = await client.post("/lessons", json={"right": "some fix"})

    assert resp.status_code == 422
