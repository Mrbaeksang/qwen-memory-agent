"""Score visualization — prove it's learning with bars."""

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
    """Effective score (reflecting success/fail) as bars — success↑/fail↓ is visible."""
    return "\n".join(
        f"{lesson['trigger']:30.30} {confidence_bar(score(lesson))}" for lesson in lessons
    )
