# Demo video script (~3 min, public on YouTube/Vimeo/Youku)

Goal: show the real loop — "stale-knowledge mistake → harvest+verify at compaction →
auto-inject into the next session → self-correction". Screen recording (terminal + Claude
Code) recommended. English narration or subtitles required.

---

### 0:00–0:25 — Problem (hook)
- Screen: in Claude Code write `from pydantic import BaseSettings` → `ImportError`.
- VO: "AI agents reason from stale training data and don't web-search. They repeat removed-API
  mistakes — and the next session doesn't know you already fixed it."

### 0:25–0:50 — Install (one command)
- Screen: `uv tool install qwen-memory-agent && qmem install` → `qmem status` (daemon UP, hooks wired).
- VO: "One command. A local daemon wires into Claude Code's lifecycle hooks — the agent never
  calls a tool."

### 0:50–1:40 — Harvest + verify (the core)
- Screen: `/compact` that session (or a PreCompact event). Show the new lesson via
  `curl localhost:8787/lessons | python3 -m json.tool`.
- Highlight: the `trigger` contains **`pydantic==2.13.4`** (the actually-installed version!) +
  the fix (`pydantic_settings`), `source: installed_package`.
- VO: "At compaction, qwen-turbo extracts the mistake; the verifier reads the actually-installed
  package on disk and qwen-plus writes a version-exact fix. No hallucination — grounded in your
  real dependency."

### 1:40–2:20 — Cross-session auto-injection
- Screen: a **new session** → ask "make a settings class with pydantic" → SessionStart /
  UserPromptSubmit injects the fix into the context (additionalContext) → the agent uses
  `pydantic_settings` from the start.
- VO: "New session, even a different tool. The fix is injected automatically — once per session.
  The same mistake never happens twice."

### 2:20–2:45 — Self-correction (forgetting)
- Screen: `uv run python demo/run_demo.py` → score bar **0.35 → 0.56 (success) → 0.28 (fail → demoted)**.
- VO: "Outcomes update a confidence score. Wrong lessons are demoted and forgotten; good ones
  rise. It gets more accurate the more you use it."

### 2:45–3:00 — Close
- Screen: architecture diagram (1s) + repo/PyPI.
- VO: "Qwen Cloud is the brain — turbo, plus with search, and rerank. Open source, on PyPI.
  Track 1: a memory that actually learns."

---

## Filming tips
- Real Qwen calls take ~10s for harvest → cut or speed up in editing.
- Zoom/highlight the version number in the lesson JSON (version-exactness is the differentiator).
- Stay under 3 minutes (judges only watch 3). English narration/subtitles.
