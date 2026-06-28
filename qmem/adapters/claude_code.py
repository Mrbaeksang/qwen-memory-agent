"""Claude Code adapter contract shim (Tier 1).

POST the host hook's stdin (JSON) to the daemon as a standard event, and turn the daemon's
response into Claude Code hook output (additionalContext). No domain logic. Daemon/input
errors must never break the host session (fail-safe: empty output, exit 0).
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from typing import Callable

# events that inject context (the rest are fire-and-forget)
INJECTING_EVENTS = {"SessionStart", "UserPromptSubmit"}

# POST signature: (path, event_dict) -> response_dict
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
        return AdapterResult("", 0)  # malformed input must not block the session either

    event = _to_event(payload)
    try:
        resp = post("/events", event) or {}
    except Exception:
        return AdapterResult("", 0)  # daemon down → pass through with empty context

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


def main() -> None:  # pragma: no cover - CLI entrypoint
    import os

    port = os.environ.get("QMEM_PORT", "8787")
    base_url = f"http://127.0.0.1:{port}"
    result = run(sys.stdin.read(), _default_poster(base_url))
    if result.stdout:
        sys.stdout.write(result.stdout)
    sys.exit(result.exit_code)


if __name__ == "__main__":  # pragma: no cover
    main()
