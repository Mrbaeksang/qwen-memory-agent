import json

from qmem.daemon.inject import build_context


async def test_session_start_injects_lesson_for_package_json_dep(client, tmp_path):
    await client.post(
        "/lessons", json={"trigger": "react | hooks", "right": "use useEffect cleanup"}
    )
    (tmp_path / "package.json").write_text(json.dumps({"dependencies": {"react": "^18"}}))

    resp = await client.post(
        "/events", json={"event": "SessionStart", "session_id": "s1", "cwd": str(tmp_path)}
    )

    assert resp.status_code == 200
    assert "react" in resp.json()["context"]


async def test_session_start_matches_requirements_txt(client, tmp_path):
    await client.post(
        "/lessons", json={"trigger": "sqlalchemy==2.0 | async", "right": "AsyncSession"}
    )
    (tmp_path / "requirements.txt").write_text("sqlalchemy>=2.0\npytest\n")

    resp = await client.post(
        "/events", json={"event": "SessionStart", "session_id": "s1", "cwd": str(tmp_path)}
    )

    assert "sqlalchemy" in resp.json()["context"]


async def test_session_start_without_matches_returns_no_context(client, tmp_path):
    (tmp_path / "package.json").write_text(json.dumps({"dependencies": {"leftpad": "1"}}))

    resp = await client.post(
        "/events", json={"event": "SessionStart", "session_id": "s1", "cwd": str(tmp_path)}
    )

    assert resp.json()["context"] is None


def test_build_context_respects_char_budget():
    lessons = [
        {"trigger": f"pkg{i} | t", "right": "x" * 100, "confidence": 0.5}
        for i in range(50)
    ]

    ctx = build_context(lessons, budget=300)

    assert len(ctx) <= 300
    assert ctx.count("[Memory") < 50  # 전부 들어가지 않음
