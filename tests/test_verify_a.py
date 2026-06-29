import json

from qmem.llm.provider import FakeProvider
from qmem.store.memory import LessonStore
from qmem.verify.package_reader import read_installed_package
from qmem.verify.verifier import verify_a


def _make_node_pkg(root, name, version, readme):
    pkg = root / "node_modules" / name
    pkg.mkdir(parents=True)
    (pkg / "package.json").write_text(json.dumps({"name": name, "version": version}))
    (pkg / "README.md").write_text(readme)


def test_read_installed_node_package(tmp_path):
    _make_node_pkg(tmp_path, "redis", "5.0.0", "use redis.asyncio for async")

    pkg = read_installed_package("redis", [tmp_path])

    assert pkg["name"] == "redis"
    assert pkg["version"] == "5.0.0"
    assert "asyncio" in pkg["docs"]


def test_read_missing_package_returns_none(tmp_path):
    assert read_installed_package("nope", [tmp_path]) is None


def test_read_global_npm_layout(tmp_path):
    # npm root -g layout: <root>/<tech>/package.json (no nested node_modules)
    pkg = tmp_path / "context-mode"
    pkg.mkdir()
    (pkg / "package.json").write_text(json.dumps({"name": "context-mode", "version": "1.0.165"}))

    result = read_installed_package("context-mode", [tmp_path])

    assert result["version"] == "1.0.165"


def test_verify_a_synthesizes_versioned_lesson(tmp_path):
    _make_node_pkg(tmp_path, "redis", "5.0.0", "use redis.asyncio")
    provider = FakeProvider(completion="Use redis.asyncio.Redis for async clients")
    candidate = {"tech": "redis", "wrong": "blocking client", "context": "async"}

    lesson = verify_a(candidate, [tmp_path], provider)

    assert lesson["trigger"] == "redis==5.0.0 | async"
    assert lesson["source"] == "installed_package"
    assert "redis.asyncio" in lesson["right"]


def test_verify_a_returns_none_when_package_absent(tmp_path):
    provider = FakeProvider(completion="x")
    lesson = verify_a({"tech": "ghost", "wrong": "y"}, [tmp_path], provider)
    assert lesson is None


def test_supersede_marks_same_trigger_stale(tmp_path):
    store = LessonStore(tmp_path / "s.db")
    old = store.create({"trigger": "redis==5.0.0 | async", "right": "old"})

    store.supersede("redis==5.0.0 | async")

    assert store.get(old["id"])["stale"] is True


async def test_precompact_verifies_and_stores_lesson(make_client, tmp_path):
    _make_node_pkg(tmp_path, "redis", "5.0.0", "use redis.asyncio")
    transcript = tmp_path / "t.jsonl"
    transcript.write_text("used redis\nError: blocking call in async context")
    provider = FakeProvider(
        by_model={
            "fake-extract": json.dumps(
                [{"tech": "redis", "wrong": "blocking client", "context": "async"}]
            ),
            "fake-chat": "Use redis.asyncio.Redis",
        }
    )

    async with make_client(provider=provider) as c:
        await c.post(
            "/events",
            json={
                "event": "PreCompact",
                "session_id": "s1",
                "transcript_path": str(transcript),
                "cwd": str(tmp_path),
            },
        )
        hits = (await c.get("/recall", params={"q": "redis"})).json()

    assert any("redis.asyncio" in h["right"] for h in hits)
    assert all(h["source"] == "installed_package" for h in hits)
