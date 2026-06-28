# CONTEXT — Qwen MemoryAgent

This document is the architecture source of truth and the project's ubiquitous-language
glossary. Design rationale lives in `docs/adr/`.

---

## One-line definition

A host-agnostic local memory daemon that fixes library/API mistakes caused by an agent's
**stale training knowledge + lack of built-in web search**: it **harvests** mistakes at
compaction time → **verifies** them against the actually-installed package version on disk →
stores them in root memory → **auto-injects** the fix into any future session of any tool,
once per session → and **self-corrects** its confidence from outcomes.

Value: *"Your coding agent uses stale APIs because it never web-searches. This memory catches
the mistake once, confirms the fix against the installed version, and injects it into every
future session. Wrong lessons demote themselves."*

---

## Ubiquitous language

| Term | Definition |
|---|---|
| **Lesson** | One verified correction. `{trigger, wrong, right, snippet, source, scope, confidence, use/success/fail, stale}` |
| **Trigger** | Lesson match key = `package@version + task` (e.g. `sqlalchemy==2.0.31 \| async test`) |
| **Harvest** | At PreCompact, scan transcript + error logs to extract "usage-mistake candidates" |
| **Verify** | Confirm the correct answer. A = read installed package (primary), B = web search (fallback) |
| **Inject** | Surface a lesson as context in a future session, without the host LLM calling a tool |
| **Reflect** | Update confidence/score from the outcome (success/fail); demote wrong lessons |
| **Root memory** | Cross-session, cross-platform shared store (`~/.qmem/mem.db`) |
| **Adapter** | Thin per-platform hook shim. POSTs events to the daemon, emits injected context on stdout |
| **Daemon** | The always-on brain. Storage / recall / harvest / verify / reflect |
| **Tier** | A platform's integration capability. 1 = hooks (full loop) / 2 = MCP / 3 = rules file |
| **Provider** | LLM backend. OpenAI-compatible abstraction, Qwen by default |

Recall score: `score = confidence × recency_decay(last_used) × (success+1)/(success+fail+2)`
(reliability uses Beta(1,1) smoothing — new = 0.5, success↑/fail↓. The naive `success/(s+f+1)`
degenerates to 0 for new lessons.)

---

## System topology

```
HOSTS (they decide; memory stays invisible)
  Claude Code[reference] · Codex · Gemini CLI · Cursor · ...
       │ lifecycle hooks (stdin: event+transcript_path / stdout: injected ctx)
  ┌────▼──────────────────────────────────────┐
  │ ADAPTER LAYER  thin per-platform hook shims │
  └────────────────┬───────────────────────────┘
                   │ HTTP localhost  fire-and-forget
  ┌────────────────▼───────────────────────────────────────────┐
  │ LOCAL DAEMON                                                │
  │  Ingress · Recall(inject) · Harvest(compact) · Reflect      │
  │  ┌───────────────────────────────────────────────────────┐ │
  │  │ MEMORY STORE  SQLite+FTS5  ~/.qmem/mem.db              │ │
  │  │ L1 Curated(always injected,~2k) · L2 Episodic(raw,FTS5)│ │
  │  │ L3 Scored(lesson body, rerank top-K injection)        │ │
  │  └───────────────────────────────────────────────────────┘ │
  │  Verifier(A: package / B: web search) · LLM Provider(Qwen)  │
  └──────┬───────────────────────────────┬─────────────────────┘
         │ DISK                          │ LLM ENDPOINT (OpenAI-compatible)
   node_modules/ site-packages/    qwen-turbo(extract) · qwen-plus(verify/synth,+search)
   (installed version = answer src)  · qwen3-rerank(recall)  | swap: OpenAI/local
```

---

## 5-stage pipeline (a lesson's lifecycle)

```
①HARVEST   PreCompact hook → transcript + in-session error logs
           → qwen-turbo extracts "usage-mistake candidates" (errors focus the prompt) [async]
②VERIFY    A. read installed package (version·types·README) ◄ primary
           B. else web search (qwen-plus enable_search) fallback
           → qwen-plus synthesizes a version-exact "recommended usage" = lesson [async]
③STORE     lesson record + FTS5 index + contradiction check (conflict → old goes stale)
④INJECT    SessionStart: read manifest (package.json/requirements.txt) and preload
           UserPromptSubmit: detect tech mention and inject
           once-per-session guarantee: injected={session_id: set(lesson_id)} → (session,lesson) at most once
           → additionalContext on stdout → host folds it into the model context (LLM-invisible)
⑤REFLECT   outcome signal (tests pass/no error = success / re-error·user fix = fail)
           → update score → below threshold archive, else prioritize ↺①
```

Weak link: **outcome attribution** is an approximation (correlation, not causation). It
converges with volume; the demo visualizes it via "test pass/fail → confidence bar".

---

## Multi-platform — three tiers

Detection is easy (an `exists` loop over config paths). The variable is integration capability:

```
TIER 1 hooks  full loop (auto-inject + harvest)  ★target
              Claude Code · Gemini CLI · Cursor · Copilot CLI · Kiro · (Qwen Code)
TIER 2 MCP    expose recall as an MCP tool (host must call, partial)
              VS Code Copilot · Zed · OpenCode · Kilo · Kimi · JetBrains · Antigravity
TIER 3 rules  static pointer in AGENTS.md (no dynamic injection, minimal)
              Aider · Cline · Goose · Warp · Windsurf
```

Detection registry (data, not code — a new platform is one table row):

| Platform | Detection path | tier |
|---|---|---|
| Claude Code | `~/.claude/settings.json` | hooks |
| Qwen Code | `~/.qwen/settings.json` | hooks |
| Gemini CLI | `~/.gemini/settings.json` | hooks |
| Codex | `~/.codex/config.toml` | mcp (hooks new) |
| Cursor | `~/.cursor/hooks.json`, `~/.cursor/mcp.json` | hooks |
| Copilot CLI | `~/.copilot/hooks/` | hooks (no precompact) |
| Zed | `~/.config/zed/settings.json` | mcp |
| Aider | `AGENTS.md` | rules |

---

## Installer

```
$ qmem install
 SCAN     resolve on-PATH `qmem`; (roadmap) scan registry detection paths
 WIRE     Claude Code: settings.json hooks → `qmem hook` (backup + additive merge)
 PLIST    launchd plist → `qmem daemon`, WorkingDirectory ~/.qmem
 DAEMON   load or kickstart; health-check http://127.0.0.1:8787
```

---

## What makes it different (vs prior art)

claude-mem · agentmemory · context-mode only "compress and replay the conversation".
Our wedge:
1. **Read the installed package directly for version-exact verification** (no staleness, no
   hallucination, offline).
2. **Scored Reflect self-correction** (wrong lessons demote = "increasingly accurate").

The plumbing (hooks, auto-detect, multi-platform) reuses prior-art patterns; effort goes into
those two.

---

## Tech stack (recommended)

```
language  Python 3.12          daemon  FastAPI + uvicorn (async)
storage   sqlite3 + FTS5       LLM     openai SDK (swap base_url)
models    qwen-turbo/plus/qwen3-rerank (dashscope-intl)
verify    importlib.metadata / node_modules parser · enable_search (fallback)
installer qmem install (uv tool install qwen-memory-agent)
```
```
scoring:  score = confidence × recency_decay × (success+1)/(success+fail+2)
```
