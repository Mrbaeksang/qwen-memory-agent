async def _prompt(client, session_id, text):
    return await client.post(
        "/events",
        json={"event": "UserPromptSubmit", "session_id": session_id, "prompt": text},
    )


async def test_injects_lesson_on_tech_mention(client):
    await client.post("/lessons", json={"trigger": "pydantic | v2", "right": "use model_config"})

    resp = await _prompt(client, "s1", "migrate this to pydantic v2")

    assert "pydantic" in resp.json()["context"]


async def test_same_lesson_not_injected_twice_in_session(client):
    await client.post("/lessons", json={"trigger": "pydantic | v2", "right": "use model_config"})

    first = await _prompt(client, "s1", "pydantic question")
    second = await _prompt(client, "s1", "pydantic again")

    assert first.json()["context"] is not None
    assert second.json()["context"] is None


async def test_independent_across_sessions(client):
    await client.post("/lessons", json={"trigger": "pydantic | v2", "right": "use model_config"})

    await _prompt(client, "s1", "pydantic")
    other = await _prompt(client, "s2", "pydantic")

    assert other.json()["context"] is not None


async def test_session_end_resets_injection_state(client):
    await client.post("/lessons", json={"trigger": "pydantic | v2", "right": "use model_config"})

    await _prompt(client, "s1", "pydantic")
    await client.post("/events", json={"event": "SessionEnd", "session_id": "s1"})
    again = await _prompt(client, "s1", "pydantic")

    assert again.json()["context"] is not None
