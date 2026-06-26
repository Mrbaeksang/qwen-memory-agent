"""회상 점수 — score = confidence × recency_decay × reliability.

reliability는 문서의 success/(success+fail+1) 대신 Beta(1,1) 평활인
(success+1)/(success+fail+2)를 쓴다. 원식은 신규 lesson(success=0)에서 0이 되어
갓 수확한 교훈이 영영 회상되지 않는 퇴화가 있다. 평활식은 신규=0.5에서 출발해
성공 누적 시 1.0으로 상승, 실패 누적 시 0.0으로 하락 — 양방향으로 움직여
"쓸수록 정확해짐"을 점수로 드러낸다.
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
