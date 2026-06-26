"""주입 컨텍스트 빌드 — 의존성 매칭 Lesson 회상 + 토큰캡."""

from qmem.store.scoring import score

INJECT_CHAR_BUDGET = 2000


def recall_for_deps(store, deps, per_dep_k: int = 5) -> list[dict]:
    seen: dict[str, dict] = {}
    for dep in deps:
        for lesson in store.recall(dep, k=per_dep_k):
            seen[lesson["id"]] = lesson
    return sorted(seen.values(), key=score, reverse=True)


def format_lesson(lesson: dict) -> str:
    right = lesson.get("right") or ""
    return f"[Memory · {lesson['trigger']}]\n⚠ {right} (confidence {lesson['confidence']:.2f})"


def build_context(lessons: list[dict], budget: int = INJECT_CHAR_BUDGET) -> str:
    blocks: list[str] = []
    used = 0
    for lesson in lessons:
        block = format_lesson(lesson)
        if blocks and used + len(block) + 1 > budget:
            break
        blocks.append(block)
        used += len(block) + 1
    return "\n".join(blocks)
