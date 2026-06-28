# ADR-0001 — Host-agnostic hook-based self-correcting memory

- Status: accepted
- Date: 2026-06-26

## Context

The first draft (README v1) was "a memory agent where Qwen makes the inline decision".
Re-defining the target value surfaced the following:

- The primary consumer is a **memory installed locally and shared by any coding platform**
  (Claude Code / Codex / Qwen Code / Cursor ...). So the inline decision is made by the host
  LLM — the memory does not decide.
- It must auto-inject/collect **without the host consciously intervening** (no tool calls).
- The real problem to solve: library/API mistakes caused by the agent's **stale training
  knowledge + lack of built-in web search**. Even after a fix in one session, **other sessions
  don't know.**
- Prior art (claude-mem, agentmemory, context-mode) already solved the "hook-based
  host-agnostic shared memory" plumbing. We can't win there.

## Decision

1. **Redefine roles**: host = decision-maker, this project = memory serving/collection,
   Qwen = memory intelligence (extract/verify/reflect/rerank).
2. **Integrate via lifecycle hooks (invisible)**. MCP is the fallback for hook-less platforms (Tier 2).
3. **Harvest trigger = PreCompact** (every major platform supports compaction; it's the moment
   right before detail is lost).
4. **Verify = read installed package (A) primary + web search (B) fallback** — the on-disk
   version is the source of truth.
5. **Harvest/outcome signal = runtime errors** (narrows harvest candidates AND serves as the
   reflect outcome signal).
6. **Provider-agnostic**: OpenAI-compatible abstraction, **Qwen by default**. qwen3-rerank /
   enable_search are Qwen advantages.
7. **Focus the wedge**: ① package verification ② scored self-correction. Reuse prior-art plumbing.
8. **Hackathon scope**: Claude Code (Tier 1) reference for the full loop. Multi-platform
   installer comes after the core.

## Consequences

- The subject of "gets more accurate with use" shifts from *the host* to *the shared memory*.
- Qwen drops the inline decision but remains central as the **background brain**, satisfying the
  track's requirement.
- Weak link: outcome attribution is correlation, not causation — converges with volume; the
  demo proves it via the test signal.
