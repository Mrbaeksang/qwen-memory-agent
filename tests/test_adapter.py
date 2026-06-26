import json
import subprocess
import sys

from qmem.adapters.claude_code import run


def test_adapter_module_runs_as_main_failsafe():
    # __main__ 가드가 연결돼 있어야 `-m` 실행이 동작한다 (회귀 방지)
    proc = subprocess.run(
        [sys.executable, "-m", "qmem.adapters.claude_code"],
        input="not json",
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert proc.returncode == 0
    assert proc.stdout == ""


def make_poster(response=None, raises=False):
    calls = []

    def post(path, event):
        calls.append((path, event))
        if raises:
            raise RuntimeError("daemon down")
        return response or {}

    post.calls = calls
    return post


def test_session_start_injects_additional_context():
    post = make_poster(response={"context": "use AsyncSession"})
    stdin = json.dumps({"hook_event_name": "SessionStart", "session_id": "s1", "cwd": "/proj"})

    result = run(stdin, post)

    assert result.exit_code == 0
    body = json.loads(result.stdout)
    assert body["hookSpecificOutput"]["hookEventName"] == "SessionStart"
    assert body["hookSpecificOutput"]["additionalContext"] == "use AsyncSession"
    # 표준 이벤트로 변환되어 POST 됨
    assert post.calls[0][0] == "/events"
    assert post.calls[0][1]["event"] == "SessionStart"
    assert post.calls[0][1]["session_id"] == "s1"


def test_precompact_is_fire_and_forget_no_stdout():
    post = make_poster(response={"context": "ignored"})
    stdin = json.dumps({"hook_event_name": "PreCompact", "session_id": "s1",
                        "transcript_path": "/t.jsonl"})

    result = run(stdin, post)

    assert result.exit_code == 0
    assert result.stdout == ""
    assert post.calls[0][1]["event"] == "PreCompact"


def test_daemon_error_is_failsafe():
    post = make_poster(raises=True)
    stdin = json.dumps({"hook_event_name": "SessionStart", "session_id": "s1"})

    result = run(stdin, post)

    assert result.exit_code == 0
    assert result.stdout == ""


def test_malformed_stdin_is_failsafe():
    post = make_poster(response={"context": "x"})

    result = run("not json at all", post)

    assert result.exit_code == 0
    assert result.stdout == ""
    assert post.calls == []


def test_injecting_event_without_context_emits_nothing():
    post = make_poster(response={})
    stdin = json.dumps({"hook_event_name": "UserPromptSubmit", "session_id": "s1",
                        "prompt": "set up sqlalchemy"})

    result = run(stdin, post)

    assert result.exit_code == 0
    assert result.stdout == ""
