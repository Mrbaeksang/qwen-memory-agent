# Devpost submission — Qwen MemoryAgent (Track 1: MemoryAgent)

> 아래 텍스트를 Devpost "Enter a Submission" 폼의 해당 칸에 붙여넣으면 됨.

## Elevator pitch (한 줄)
A self-correcting memory that stops your coding agent from repeating stale-knowledge library mistakes — across sessions and across tools.

## Inspiration
AI coding agents reason from **stale training knowledge** and don't web-search by default, so they keep using removed/old library APIs (e.g. `from pydantic import BaseSettings`, `openai.ChatCompletion.create`). The real pain: even after you correct it once, the **next session — or a different tool — doesn't know.** The same trap, forever.

## What it does
A local, host-agnostic memory daemon that, with **no manual action from the agent**:
1. **Harvests** library/API mistakes from a session at **compaction time** (the one lifecycle event every agent supports).
2. **Verifies the fix against the actually-installed package on disk** (version-exact, no hallucination) — falling back to web search only when the package isn't found.
3. Stores a scored **Lesson** in a shared root memory.
4. **Auto-injects** the relevant fix into any future session of any tool — once per session.
5. **Self-corrects**: outcomes update a confidence score, so wrong lessons are demoted and forgotten while good ones rise.

## How we built it
- **Daemon**: FastAPI on `127.0.0.1:8787`; root memory in **SQLite + FTS5** (keyword recall at zero embedding cost), scored recall on top.
- **Integration**: Claude Code **lifecycle hooks** (SessionStart / UserPromptSubmit / PreCompact / SessionEnd) via a thin, fail-safe adapter — the host LLM never has to call a tool, so injection is automatic.
- **Qwen Cloud (Alibaba Cloud)** does all the memory intelligence: `qwen-turbo` extracts mistake candidates, `qwen-plus` (with `enable_search`) synthesizes the verified fix, `qwen3-rerank` ranks recall. OpenAI-compatible via DashScope — provider-pluggable, Qwen by default.
- **Verifier**: reads the installed package's version + docs from `node_modules` / `site-packages` to ground the correction in the exact installed version.
- **Reflect**: `score = confidence × recency_decay × (success+1)/(success+fail+2)` (Beta smoothing so new lessons start neutral and move both ways).
- TDD throughout (52 tests), packaged to **PyPI** (`qwen-memory-agent`), one-command install, **PyPI Trusted Publishing (OIDC)** CI.

## Alibaba Cloud usage (Proof of Deployment)
Qwen Cloud / DashScope is the backend brain. Code file demonstrating Alibaba Cloud API usage:
`qmem/llm/provider.py` — `QwenProvider` calls `https://dashscope-intl.aliyuncs.com/compatible-mode/v1` (chat + `enable_search` + `qwen3-rerank`).

## Challenges
- Making injection **host-invisible** → solved with lifecycle hooks + `additionalContext`, not MCP tool calls.
- **Trusting** a correction → read the installed package instead of trusting the LLM's memory; reflect demotes wrong ones.
- Real-LLM robustness → real Qwen wraps JSON in code fences; we slice the array out before parsing.
- Token safety on huge (1M ctx) sessions → cap transcript sent for harvest.

## Accomplishments
- A memory that is **version-accurate** (proven live: generated `openai==2.44.0` and `pydantic==2.13.4` fixes from the actually-installed versions) and **self-correcting** — beyond "store & replay" tools.
- End-to-end working, installable in one command, published on PyPI, 52 tests green.

## What we learned
Honest weak link is **outcome attribution** (success/fail is correlation, not causation) — it converges with volume; the installed-package verification is what makes the stored knowledge trustworthy.

## What's next
Multi-platform auto-detecting installer (Codex/Gemini/Cursor adapters across hook/MCP/rules tiers); confidence-driven L1 promotion.

## Built with
Python · FastAPI · SQLite/FTS5 · Qwen Cloud (DashScope: qwen-turbo / qwen-plus / qwen3-rerank) · OpenAI SDK · Claude Code hooks · uv · launchd · GitHub Actions (OIDC Trusted Publishing)

## Try it (testing instructions for judges)
```bash
uv tool install qwen-memory-agent      # macOS
qmem install                           # wires Claude Code hooks + starts daemon
# offline, no key needed — see the full loop:
git clone https://github.com/Mrbaeksang/qwen-memory-agent && cd qwen-memory-agent
uv sync && uv run pytest               # 52 tests
uv run python demo/run_demo.py         # cross-session learning demo (ON vs OFF)
```
Repo: https://github.com/Mrbaeksang/qwen-memory-agent · License: MIT
