# Qwen MemoryAgent

쓸수록 정확해지는(self-improving) 영속 메모리 에이전트. Qwen Cloud 기반. 자세한 설계는 `README.md` 참고.

## Agent skills

### Issue tracker

Issues are tracked as GitHub issues via the `gh` CLI (repo: `Mrbaeksang/qwen-memory-agent`). External PRs are **not** a triage surface. See `docs/agents/issue-tracker.md`.

### Triage labels

Five canonical triage roles, each mapped to its identically-named label (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context layout — one `CONTEXT.md` + `docs/adr/` at the repo root. See `docs/agents/domain.md`.
