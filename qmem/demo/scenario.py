"""End-to-end demo — session 1 harvests a mistake → Lesson, session 2 injects it cross-session.

Contrasts memory ON/OFF to show "more accurate with use".
"""

from qmem.daemon.harvest import harvest
from qmem.daemon.inject import build_context, recall_for_deps
from qmem.daemon.manifest import read_dependencies
from qmem.verify.verifier import verify_and_store


def run_scenario(store, provider, project_dir: str, transcript_text: str) -> dict:
    # session 1: PreCompact harvest + Verify-A → store Lesson
    candidates = harvest(transcript_text, provider)
    created = verify_and_store(candidates, [project_dir], provider, store)

    # session 2 (restart / cross-session): SessionStart preload injection
    deps = read_dependencies(project_dir)
    lessons = recall_for_deps(store, deps)
    session2_on = build_context(lessons)
    session2_off = ""  # no injection when memory is disabled

    return {
        "created": created,
        "session2_on": session2_on,
        "session2_off": session2_off,
        "lessons": lessons,
    }
