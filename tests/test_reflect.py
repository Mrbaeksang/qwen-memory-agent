from qmem.store.scoring import reliability


async def _outcome(client, lesson_id, success):
    return await client.post(
        "/events", json={"event": "Outcome", "lesson_id": lesson_id, "success": success}
    )


async def test_success_increments_success_count(client):
    lesson = (await client.post("/lessons", json={"trigger": "x | t", "right": "r"})).json()

    await _outcome(client, lesson["id"], True)

    got = (await client.get(f"/lessons/{lesson['id']}")).json()
    assert got["success_count"] == 1
    assert got["use_count"] == 1


async def test_fail_increments_fail_count(client):
    lesson = (await client.post("/lessons", json={"trigger": "x | t", "right": "r"})).json()

    await _outcome(client, lesson["id"], False)

    got = (await client.get(f"/lessons/{lesson['id']}")).json()
    assert got["fail_count"] == 1


async def test_repeated_failures_archive_and_drop_from_recall(client):
    lesson = (
        await client.post("/lessons", json={"trigger": "flaky | t", "right": "r", "confidence": 0.7})
    ).json()

    for _ in range(5):
        await _outcome(client, lesson["id"], False)

    got = (await client.get(f"/lessons/{lesson['id']}")).json()
    assert got["archived"] is True
    hits = (await client.get("/recall", params={"q": "flaky"})).json()
    assert hits == []


def test_reliability_moves_both_directions():
    # 성공은 올리고 실패는 내린다 (신규 0.5에서 출발)
    assert reliability(3, 0) > reliability(0, 0) > reliability(0, 3)
