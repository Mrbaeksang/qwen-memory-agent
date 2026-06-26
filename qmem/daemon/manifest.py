"""프로젝트 매니페스트에서 의존성 이름을 추출 (주입 대상 선정용)."""

import json
import re
from pathlib import Path


def read_dependencies(cwd: str | Path) -> set[str]:
    deps: set[str] = set()
    root = Path(cwd)

    pj = root / "package.json"
    if pj.exists():
        try:
            data = json.loads(pj.read_text())
            for key in ("dependencies", "devDependencies"):
                deps.update((data.get(key) or {}).keys())
        except Exception:
            pass

    rt = root / "requirements.txt"
    if rt.exists():
        try:
            for raw in rt.read_text().splitlines():
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                name = re.split(r"[=<>!~\[ ]", line)[0]
                if name:
                    deps.add(name)
        except Exception:
            pass

    return deps
