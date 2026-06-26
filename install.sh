#!/usr/bin/env bash
# qmem 원스크립트 설치(레포 개발용) — 의존성 설치 후 CLI 설치 위임.
# PyPI 사용자는:  uv tool install qwen-memory-agent && qmem install
set -euo pipefail
cd "$(dirname "$0")"

echo "==> 의존성 설치 (uv sync)"
uv sync

echo "==> qmem install (훅 와이어링 + 데몬 기동)"
uv run qmem install
