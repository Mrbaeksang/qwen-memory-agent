#!/usr/bin/env bash
# Visible demo choreography for the headless-screencast recording (qmem).
# Assumes on the Linux box: repo cloned + `uv sync` (so .venv has pydantic),
#   `qmem install` run (daemon up on :8787), QWEN_API_KEY set in ~/.qmem/.env.
# Env: REPO (repo dir), SENTINEL (done-flag path), PORT (default 8787).
set -u
export PYTHONWARNINGS=ignore
REPO="${REPO:-$HOME/qwen-memory-agent}"
SENTINEL="${SENTINEL:-/tmp/qmem_demo.done}"
PORT="${PORT:-8787}"

type_run() { printf '\n\033[1;35m$ %s\033[0m\n' "$*"; sleep 0.6; eval "$*"; sleep 1.3; }
say()      { printf '\n\033[1;36m# %s\033[0m\n' "$*"; sleep 1.0; }

clear
say "Qwen MemoryAgent  —  self-correcting memory for coding agents"
sleep 1

say "1) Daemon + Claude Code hooks are installed"
type_run "qmem status"

say "2) An agent just used a STALE API (pydantic v2 removed BaseSettings)"
TR=$(mktemp)
printf 'user: make an app Settings class\nassistant: from pydantic import BaseSettings\nImportError: BaseSettings has moved to the pydantic-settings package\n' > "$TR"
type_run "cat $TR"

say "3) On compaction, qmem harvests it and VERIFIES against the installed pydantic"
type_run "curl -s -X POST localhost:$PORT/events -H 'content-type: application/json' -d '{\"event\":\"PreCompact\",\"session_id\":\"demo\",\"transcript_path\":\"$TR\",\"cwd\":\"$REPO\"}' >/dev/null"
printf "   Qwen working"
for _ in $(seq 1 25); do
  n=$(curl -s "localhost:$PORT/lessons" | python3 -c 'import sys,json;print(len(json.load(sys.stdin)))' 2>/dev/null)
  [ "${n:-0}" -gt 0 ] && break
  printf "."; sleep 2
done
printf " done\n"; sleep 0.5
type_run "curl -s localhost:$PORT/lessons | python3 -m json.tool"
say "   ^ trigger pinned to the ACTUAL installed version  ·  source: installed_package (no hallucination)"

say "4) Next session — the fix is auto-injected (host never calls a tool)"
type_run "echo '{\"hook_event_name\":\"UserPromptSubmit\",\"session_id\":\"next\",\"prompt\":\"make a settings class with pydantic\"}' | qmem hook | python3 -m json.tool"

say "5) Self-correction — score rises on success, falls on failure, wrong lessons get forgotten"
type_run "python3 $REPO/demo/run_demo.py"

say "Open source  ·  pip install:  uv tool install qwen-memory-agent"
sleep 2
touch "$SENTINEL"
