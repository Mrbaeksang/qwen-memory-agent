"""런타임 설정 — .env 로딩, 루트 메모리 경로, Qwen provider 구성."""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PORT = 8787


def load_dotenv(path: Path | None = None) -> None:
    path = path or (PROJECT_ROOT / ".env")
    if not path.exists():
        return
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def default_db_path() -> Path:
    p = Path.home() / ".qmem" / "mem.db"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def port() -> int:
    return int(os.environ.get("QMEM_PORT", DEFAULT_PORT))


def build_provider():
    """환경변수에서 Qwen provider를 구성 (키 없으면 그대로, 호출 시 실패)."""
    from qmem.llm.provider import QwenProvider

    return QwenProvider(
        api_key=os.environ.get("QWEN_API_KEY"),
        base_url=os.environ.get(
            "QWEN_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
        ),
        chat_model=os.environ.get("QWEN_MODEL_INLINE", "qwen-plus"),
        extract_model=os.environ.get("QWEN_MODEL_REVIEW", "qwen-turbo"),
    )
