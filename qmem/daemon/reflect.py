"""Reflect — update scores from outcome signals and archive (forget) sub-threshold lessons."""

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
