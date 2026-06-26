"""점수 시각화 — 학습 중임을 막대로 증명."""

from qmem.store.scoring import score


def confidence_bar(value: float, width: int = 20) -> str:
    value = max(0.0, min(1.0, value))
    filled = round(value * width)
    return "█" * filled + "░" * (width - filled) + f" {value:.2f}"


def render_confidence_bars(lessons: list[dict]) -> str:
    return "\n".join(
        f"{lesson['trigger']:30.30} {confidence_bar(lesson['confidence'])}"
        for lesson in lessons
    )


def render_score_bars(lessons: list[dict]) -> str:
    """효과 점수(success/fail 반영)를 막대로 — 성공↑/실패↓가 눈에 보인다."""
    return "\n".join(
        f"{lesson['trigger']:30.30} {confidence_bar(score(lesson))}" for lesson in lessons
    )
