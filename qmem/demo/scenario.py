"""엔드투엔드 데모 — 세션1 실수 수확→Lesson, 세션2 크로스세션 주입.

메모리 ON/OFF 대비로 "쓸수록 정확해짐"을 보여준다.
"""

from qmem.daemon.harvest import harvest
from qmem.daemon.inject import build_context, recall_for_deps
from qmem.daemon.manifest import read_dependencies
from qmem.verify.verifier import verify_and_store


def run_scenario(store, provider, project_dir: str, transcript_text: str) -> dict:
    # 세션 1: PreCompact 수확 + Verify-A → Lesson 저장
    candidates = harvest(transcript_text, provider)
    created = verify_and_store(candidates, [project_dir], provider, store)

    # 세션 2 (재시작/크로스세션): SessionStart 프리로드 주입
    deps = read_dependencies(project_dir)
    lessons = recall_for_deps(store, deps)
    session2_on = build_context(lessons)
    session2_off = ""  # 메모리 비활성 시 주입 없음

    return {
        "created": created,
        "session2_on": session2_on,
        "session2_off": session2_off,
        "lessons": lessons,
    }
