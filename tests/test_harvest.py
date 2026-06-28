import json

from qmem.daemon.harvest import extract_errors, harvest
from qmem.llm.provider import FakeProvider


def test_harvest_extracts_candidates_from_transcript():
    candidates = [{"tech": "sqlalchemy", "wrong": "sync Session", "context": "async test"}]
    provider = FakeProvider(completion=json.dumps(candidates))

    out = harvest("session text\nError: boom", provider)

    assert out == candidates


def test_harvest_tolerates_markdown_fenced_json():
    candidates = [{"tech": "pydantic", "wrong": "BaseSettings import", "context": "config"}]
    fenced = "```json\n" + json.dumps(candidates) + "\n```"
    provider = FakeProvider(completion=fenced)

    assert harvest("some session\nImportError: boom", provider) == candidates


def test_harvest_invalid_json_returns_empty():
    provider = FakeProvider(completion="sorry, no JSON here")

    assert harvest("some text", provider) == []


def test_harvest_empty_transcript_skips_provider():
    provider = FakeProvider(completion="[]")

    assert harvest("   ", provider) == []
    assert provider.calls == []  # empty transcript → no LLM call


def test_extract_errors_finds_error_lines():
    text = "ok line\nTraceback (most recent call last)\nValueError: bad\nfine"

    errs = extract_errors(text)

    assert any("Traceback" in e for e in errs)
    assert any("ValueError" in e for e in errs)


async def test_precompact_records_candidates_async(make_client, tmp_path):
    candidates = [{"tech": "redis", "wrong": "blocking client", "context": "async"}]
    provider = FakeProvider(completion=json.dumps(candidates))
    transcript = tmp_path / "t.jsonl"
    transcript.write_text("used redis\nError: blocking call in async context")

    async with make_client(provider=provider) as c:
        resp = await c.post(
            "/events",
            json={
                "event": "PreCompact",
                "session_id": "s1",
                "transcript_path": str(transcript),
            },
        )
        assert resp.status_code == 200
        pending = (await c.get("/pending")).json()

    assert pending == candidates
