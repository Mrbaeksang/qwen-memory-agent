"""Reflect — 결과 신호로 점수를 갱신하고 임계치 미만 Lesson을 archive(망각)."""

from qmem.store.scoring import score

ARCHIVE_THRESHOLD = 0.15


def apply_result(store, lesson_id: str, success: bool) -> dict | None:
    lesson = store.apply_outcome(lesson_id, success)
    if lesson is None:
        return None
    if not success and score(lesson) < ARCHIVE_THRESHOLD:
        store.set_archived(lesson_id)
        lesson = store.get(lesson_id)
    return lesson
