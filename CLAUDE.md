# Qwen MemoryAgent

A self-improving persistent memory agent that gets more accurate with use. Powered by Qwen Cloud. See `README.md` for the design.

## Agent skills

### Issue tracker

Issues are tracked as GitHub issues via the `gh` CLI (repo: `Mrbaeksang/qwen-memory-agent`). External PRs are **not** a triage surface. See `docs/agents/issue-tracker.md`.

### Triage labels

Five canonical triage roles, each mapped to its identically-named label (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context layout — one `CONTEXT.md` + `docs/adr/` at the repo root. See `docs/agents/domain.md`.
