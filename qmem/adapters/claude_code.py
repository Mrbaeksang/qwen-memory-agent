"""Claude Code 어댑터 contract shim (Tier 1).

호스트 훅 stdin(JSON)을 표준 이벤트로 데몬에 POST하고, 데몬 응답을
Claude Code 훅 출력(additionalContext)으로 변환한다. 도메인 로직 없음.
데몬/입력 오류는 절대 호스트 세션을 깨뜨리지 않는다(fail-safe: 빈 출력, exit 0).
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from typing import Callable

# 컨텍스트를 주입하는 이벤트 (그 외는 fire-and-forget)
INJECTING_EVENTS = {"SessionStart", "UserPromptSubmit"}

# POST 시그니처: (path, event_dict) -> response_dict
Poster = Callable[[str, dict], dict]


@dataclass
class AdapterResult:
    stdout: str
    exit_code: int


def _to_event(payload: dict) -> dict:
    return {
        "event": payload.get("hook_event_name"),
        "session_id": payload.get("session_id"),
        "transcript_path": payload.get("transcript_path"),
        "cwd": payload.get("cwd"),
        "prompt": payload.get("prompt"),
    }


def run(stdin_text: str, post: Poster) -> AdapterResult:
    try:
        payload = json.loads(stdin_text)
    except Exception:
        return AdapterResult("", 0)  # 깨진 입력도 세션을 막지 않음

    event = _to_event(payload)
    try:
        resp = post("/events", event) or {}
    except Exception:
        return AdapterResult("", 0)  # 데몬 다운 → 빈 컨텍스트로 통과

    if event["event"] in INJECTING_EVENTS:
        context = resp.get("context")
        if context:
            out = json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": event["event"],
                        "additionalContext": context,
                    }
                }
            )
            return AdapterResult(out, 0)

    return AdapterResult("", 0)


def _default_poster(base_url: str) -> Poster:
    import httpx

    def post(path: str, event: dict) -> dict:
        resp = httpx.post(base_url + path, json=event, timeout=3)
        resp.raise_for_status()
        return resp.json() if resp.content else {}

    return post


def main() -> None:  # pragma: no cover - CLI 진입점
    import os

    port = os.environ.get("QMEM_PORT", "8787")
    base_url = f"http://127.0.0.1:{port}"
    result = run(sys.stdin.read(), _default_poster(base_url))
    if result.stdout:
        sys.stdout.write(result.stdout)
    sys.exit(result.exit_code)


if __name__ == "__main__":  # pragma: no cover
    main()
