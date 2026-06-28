#!/usr/bin/env bash
# qmem one-script install (for repo development) — sync deps, then delegate to the CLI.
# PyPI users:  uv tool install qwen-memory-agent && qmem install
set -euo pipefail
cd "$(dirname "$0")"

echo "==> install dependencies (uv sync)"
uv sync

echo "==> qmem install (wire hooks + start daemon)"
uv run qmem install
