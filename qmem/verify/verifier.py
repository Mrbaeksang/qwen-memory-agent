"""Verify-A — 설치 패키지를 읽어 버전-정확한 Lesson을 합성하고 저장."""

from qmem.verify.package_reader import read_installed_package

VERIFY_INSTRUCTION = (
    "Given the installed package docs and the observed mistake, state the correct "
    "current recommended usage in one or two sentences.\n\n"
)

WEB_INSTRUCTION = (
    "Search the web for the current recommended usage and correct this mistake "
    "in one or two sentences.\n\n"
)


def verify_b(candidate: dict, provider) -> dict | None:
    """Verify-A가 디스크에서 못 찾을 때 웹서치 폴백. 미지원 프로바이더는 degrade(None)."""
    if not provider.supports_web_search:
        return None
    prompt = (
        WEB_INSTRUCTION
        + f"TECH: {candidate.get('tech')}\n"
        + f"MISTAKE: {candidate.get('wrong')}\n"
        + f"CONTEXT: {candidate.get('context')}"
    )
    right = provider.complete(prompt, model=provider.config.chat_model, web_search=True)
    trigger = f"{candidate.get('tech', '')} | {candidate.get('context', '')}".strip()
    return {
        "trigger": trigger,
        "wrong": candidate.get("wrong"),
        "right": right,
        "source": "web_search",
    }


def verify_a(candidate: dict, search_paths: list, provider) -> dict | None:
    pkg = read_installed_package(candidate.get("tech", ""), search_paths)
    if pkg is None:
        return None
    prompt = (
        VERIFY_INSTRUCTION
        + f"PACKAGE: {pkg['name']}=={pkg['version']}\n"
        + f"DOCS:\n{pkg['docs']}\n"
        + f"MISTAKE: {candidate.get('wrong')}\n"
        + f"CONTEXT: {candidate.get('context')}"
    )
    right = provider.complete(prompt, model=provider.config.chat_model)
    trigger = f"{pkg['name']}=={pkg['version']} | {candidate.get('context', '')}".strip()
    return {
        "trigger": trigger,
        "wrong": candidate.get("wrong"),
        "right": right,
        "source": "installed_package",
    }


def verify_and_store(candidates: list[dict], search_paths: list, provider, store) -> list[dict]:
    created = []
    for cand in candidates:
        lesson = verify_a(cand, search_paths, provider) or verify_b(cand, provider)
        if lesson is not None:
            store.supersede(lesson["trigger"])  # 모순/갱신: 같은 trigger 옛것 stale
            created.append(store.create(lesson))
    return created
