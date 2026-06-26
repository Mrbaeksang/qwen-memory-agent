"""PreCompact harvest — transcript + 에러 신호에서 사용법 실수 후보 추출."""

import json
from pathlib import Path

ERROR_MARKERS = ("Error", "Traceback", "Exception", "error:")

HARVEST_INSTRUCTION = (
    "Extract library/API usage mistakes from this coding session transcript. "
    "Return a JSON array of objects with keys: tech, wrong, context. "
    "Only include genuine mistakes tied to a library or dependency.\n\nTRANSCRIPT:\n"
)


def read_transcript(path: str | None) -> str:
    if not path:
        return ""
    p = Path(path)
    if not p.exists():
        return ""
    try:
        return p.read_text()
    except Exception:
        return ""


def extract_errors(transcript_text: str) -> list[str]:
    return [
        line
        for line in transcript_text.splitlines()
        if any(marker in line for marker in ERROR_MARKERS)
    ]


def harvest(transcript_text: str, provider) -> list[dict]:
    if not transcript_text.strip():
        return []
    errors = extract_errors(transcript_text)
    focus = ("\n\nERROR LINES (focus here):\n" + "\n".join(errors)) if errors else ""
    raw = provider.complete(
        HARVEST_INSTRUCTION + transcript_text + focus,
        model=provider.config.extract_model,
    )
    try:
        data = json.loads(raw)
    except Exception:
        return []
    return data if isinstance(data, list) else []
