"""설치된 패키지를 디스크에서 직접 읽어 버전·문서를 얻는다 (Verify-A 정답 출처)."""

import json
from pathlib import Path


def read_installed_package(tech: str, search_paths: list[str | Path]) -> dict | None:
    if not tech:
        return None
    for base in search_paths:
        base = Path(base)

        # Node — node_modules/<tech>/package.json (+ README)
        pj = base / "node_modules" / tech / "package.json"
        if pj.exists():
            try:
                version = json.loads(pj.read_text()).get("version", "")
            except Exception:
                version = ""
            docs = ""
            for readme in ("README.md", "readme.md"):
                rp = base / "node_modules" / tech / readme
                if rp.exists():
                    docs = rp.read_text()
                    break
            return {"name": tech, "version": version, "docs": docs}

        # Python — site-packages/<tech>-<ver>.dist-info/METADATA
        for dist in base.glob(f"{tech}-*.dist-info"):
            meta = dist / "METADATA"
            if not meta.exists():
                continue
            text = meta.read_text()
            version = ""
            for line in text.splitlines():
                if line.startswith("Version:"):
                    version = line.split(":", 1)[1].strip()
                    break
            return {"name": tech, "version": version, "docs": text}

    return None
