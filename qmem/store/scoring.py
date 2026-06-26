"""회상 점수 — score = confidence × recency_decay × reliability.

reliability는 문서의 success/(success+fail+1)을 Laplace 평활한
(success+1)/(success+fail+1) 형태를 쓴다. 원식은 신규 lesson(success=0)에서
0이 되어 갓 수확한 교훈이 영영 회상되지 않는 퇴화가 있어 이를 보정한다.
신규=1.0, 실패 누적 시 하락, 성공 누적 시 1.0 유지.
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
    return (success_count + 1) / (success_count + fail_count + 1)


def score(lesson: dict, now: datetime | None = None) -> float:
    return (
        lesson["confidence"]
        * recency_decay(lesson.get("last_used"), lesson["created_at"], now)
        * reliability(lesson["success_count"], lesson["fail_count"])
    )
