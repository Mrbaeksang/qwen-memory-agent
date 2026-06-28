"""Runtime config — .env loading, root-memory path, Qwen provider construction."""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
QMEM_HOME = Path.home() / ".qmem"
DEFAULT_PORT = 8787


def _apply_env_file(path: Path) -> None:
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def load_dotenv(path: Path | None = None) -> None:
    """Load the first .env that exists: ~/.qmem/.env → repo .env → cwd/.env."""
    candidates = [path] if path else [QMEM_HOME / ".env", PROJECT_ROOT / ".env", Path.cwd() / ".env"]
    for candidate in candidates:
        if candidate and candidate.exists():
            _apply_env_file(candidate)
            return


def default_db_path() -> Path:
    QMEM_HOME.mkdir(parents=True, exist_ok=True)
    return QMEM_HOME / "mem.db"


def port() -> int:
    return int(os.environ.get("QMEM_PORT", DEFAULT_PORT))


def build_provider():
    """Build a Qwen provider from env vars (no key → constructs anyway, fails on call)."""
    from qmem.llm.provider import QwenProvider

    return QwenProvider(
        api_key=os.environ.get("QWEN_API_KEY"),
        base_url=os.environ.get(
            "QWEN_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
        ),
        chat_model=os.environ.get("QWEN_MODEL_INLINE", "qwen-plus"),
        extract_model=os.environ.get("QWEN_MODEL_REVIEW", "qwen-turbo"),
    )
