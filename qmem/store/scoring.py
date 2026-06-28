"""Recall score — score = confidence × recency_decay × reliability.

reliability uses Beta(1,1) smoothing (success+1)/(success+fail+2) instead of the naive
success/(success+fail+1). The naive form degenerates to 0 for a new lesson (success=0),
so a freshly harvested lesson would never be recalled. The smoothed form starts at 0.5,
rises toward 1.0 with successes and falls toward 0.0 with failures — moving both ways so
"more accurate with use" shows up in the score.
"""

from datetime import datetime, timezone

HALF_LIFE_DAYS = 30.0


def _parse(ts: str) -> datetime:
    return datetime.fromisoformat(ts)


def recency_decay(last_used: str | None, created_at: str, now: datetime | None = None) -> float:
    now = now or datetime.now(timezone.utc)
    ref = _parse(last_used or created_at)
    age_days = max(0.0, (now - ref).total_seconds() / 86400.0)
    return 0.5 ** (age_days / HALF_LIFE_DAYS)


def reliability(success_count: int, fail_count: int) -> float:
    return (success_count + 1) / (success_count + fail_count + 2)


def score(lesson: dict, now: datetime | None = None) -> float:
    return (
        lesson["confidence"]
        * recency_decay(lesson.get("last_used"), lesson["created_at"], now)
        * reliability(lesson["success_count"], lesson["fail_count"])
    )
