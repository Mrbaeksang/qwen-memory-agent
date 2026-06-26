# Qwen MemoryAgent

> **Global AI Hackathon Series with Qwen Cloud — Track 1: MemoryAgent**
> 낡은 학습지식 때문에 라이브러리 실수를 반복하는 코딩 에이전트를, **쓸수록 정확해지게** 만드는
> host-agnostic 자가교정 메모리. Qwen Cloud 기반.

[![PyPI](https://img.shields.io/pypi/v/qwen-memory-agent)](https://pypi.org/project/qwen-memory-agent/)

```bash
uv tool install qwen-memory-agent && qmem install   # macOS / Claude Code
```

---

## 문제

AI 코딩 에이전트는 **학습된(낡은) 지식**으로 라이브러리/의존성을 다루다 실수한다. 웹서치를
기본 동봉하지 않으니 최신 API를 모른다. 결정적으로 — **한 세션에서 그 실수를 교정해도
다음/다른 세션은 그걸 모른다.** 같은 함정에 매번 다시 빠진다.

## 효용

> 네 코딩 에이전트는 웹서치를 안 해서 낡은 API로 틀린다. 이 메모리는 그 실수를 **compact
> 순간에 잡아 — 디스크에 깔린 실제 버전을 뜯어 정답을 확인해두고 — 모든 플랫폼의 모든 미래
> 세션에 세션당 1회 자동 주입한다. 틀리면 스스로 도태시킨다.**

핵심은 단순 저장이 아니라 **(1) 실수 수확 · (2) 버전-정확 검증 · (3) 무개입 주입 · (4) 자가 교정**.

---

## 아키텍처 (요약 — 정본은 [`CONTEXT.md`](./CONTEXT.md))

```
HOSTS (결정은 얘들이, 메모리에 무개입)
  Claude Code · Codex · Gemini CLI · Cursor · ...
       │ 라이프사이클 훅
  ADAPTER LAYER  (플랫폼별 얇은 훅 스크립트)
       │ HTTP localhost
  LOCAL DAEMON  ── Ingress · Recall · Harvest · Reflect
       ├─ MEMORY STORE  SQLite+FTS5  (~/.qmem/mem.db)
       │     L1 Curated(항상주입) · L2 Episodic(원문/FTS5) · L3 Scored(lesson/rerank)
       ├─ Verifier   A:설치패키지 뜯기(우선) / B:웹서치(폴백)
       └─ LLM Provider  Qwen 기본 (qwen-turbo/plus/qwen3-rerank) · 교체 가능
```

### 5단계 파이프라인

```
①HARVEST  PreCompact 훅 → transcript+에러로그 → qwen-turbo가 실수후보 추출 [async]
②VERIFY   설치패키지 뜯기(A,우선) → 없으면 웹서치(B) → qwen-plus가 정답=lesson 합성 [async]
③STORE    lesson + FTS5 인덱싱 + 모순체크(충돌→stale)
④INJECT   SessionStart/UserPromptSubmit 훅 → 세션당 1회 자동 주입 (LLM 무개입)
⑤REFLECT  결과신호(테스트통과/실패) → score 갱신 → 도태/우선주입 ↺①
```

`score = confidence × recency_decay(last_used) × (success+1)/(success+fail+2)`
*(reliability는 Beta(1,1) 평활 — 신규 0.5에서 성공↑/실패↓ 양방향 이동. 원식 `success/(s+f+1)`은 신규가 0이 되는 퇴화가 있어 보정.)*

---

## 차별점 (vs claude-mem · agentmemory · context-mode)

기존 툴은 "대화를 압축 저장/주입"까지만 한다. 본 프로젝트의 wedge:

| | 본 프로젝트 | 기존 툴 |
|---|---|---|
| 검증 | **설치 패키지를 직접 뜯어 버전-정확** (환각 0) | 대화 요약 저장 |
| 학습 | **점수형 Reflect 자가교정** (틀린 lesson 도태) | 없음 |

플러밍(훅·자동감지·멀티플랫폼)은 prior art 패턴을 차용하고, 시간은 위 둘에 집중.

---

## 멀티플랫폼

**현재 구현**: `qmem install`이 Claude Code(Tier1) 훅(SessionStart/UserPromptSubmit/PreCompact/
SessionEnd)을 와이어링한다 — 풀루프 동작. 데몬은 플랫폼 중립(HTTP)이라 다른 호스트는 어댑터만 추가.

**로드맵(설계)**: 설정경로 스캔으로 깔린 플랫폼 자동감지 + 대화형 선택 + 등급별 와이어링.
플랫폼마다 통합 가능 등급이 다르다:

```
TIER 1 훅   풀루프(자동주입+수확)  ← Claude Code [구현] · Gemini CLI · Cursor · Copilot CLI · Kiro
TIER 2 MCP  recall을 MCP 툴 노출   ← Zed · OpenCode · VS Code Copilot · JetBrains ...
TIER 3 룰   AGENTS.md 정적 포인터  ← Aider · Cline · Goose · Warp ...
```

---

## Qwen 모델 배분 (비종속, Qwen 기본 권장)

| 용도 | 모델 |
|---|---|
| 실수 후보 추출 (대량) | `qwen-turbo` |
| 검증/lesson 합성 (+웹서치) | `qwen-plus` (`enable_search`) |
| 회상 재정렬 | `qwen3-rerank` |
| L2 키워드 검색 | LLM 미사용 (FTS5) |

**Qwen 쓰면 풀스택, 타 프로바이더는 코어(rerank/웹서치 차등).**
**API**: OpenAI 호환 — `base_url=https://dashscope-intl.aliyuncs.com/compatible-mode/v1`

---

## 심사 기준 매핑

| 심사 기준 | 구현 |
|---|---|
| ① 효율 저장/검색 | L2 FTS5(임베딩 0) + L3 점수 랭킹 + qwen3-rerank |
| ② 적시 망각 | 모순 stale + 점수 감쇠 archive + 용량 통합 |
| ③ 제한 컨텍스트 회상 | L1 토큰캡 + rerank top-K + 세션당 1회 주입 |
| **increasingly accurate** | 패키지-검증 + Reflect success/fail 점수 교정 |

---

## 빌드 단계

- [x] **P1** — SQLite+FTS5 스키마, lesson CRUD/검색 (L2/L3) — #2 #3
- [x] **P2** — Claude Code 어댑터: SessionStart/UserPromptSubmit 주입 (세션당 1회) — #5 #6 #7
- [x] **P3** — PreCompact 수확 → Verifier(패키지 뜯기 A) → lesson 합성 — #8 #9
- [x] **P4** — Reflect 점수 루프 + 웹서치 폴백(B) *(차별화 핵심)* — #4 #10 #11
- [x] **P5** — 데모 시나리오 + confidence 시각화 — #12
- [~] **P6** — 설치기: Claude Code(Tier1) 훅 + launchd 데몬 + `qmem` CLI + **PyPI 배포** 완료 / 멀티플랫폼 자동감지·대화형은 다음

> 코어(P1~P5) 구현 완료 · **PyPI v0.1.0 배포** · `uv run pytest` **52 passed** · `uv run python demo/run_demo.py`로 크로스세션 학습 데모 실행.

---

## 실사용 설치 (Claude Code)

**PyPI (권장)** — 레포 클론 없이:
```bash
uv tool install qwen-memory-agent   # 또는 pipx install qwen-memory-agent
qmem install                        # 훅 와이어링 + 데몬 기동
# ~/.qmem/.env 에 QWEN_API_KEY 입력 후: qmem install 재실행(또는 데몬 재기동)
```
명령: `qmem install` / `qmem uninstall` / `qmem status` / `qmem daemon` / `qmem hook`

**레포에서(개발)** — 원스크립트:
```bash
git clone https://github.com/Mrbaeksang/qwen-memory-agent && cd qwen-memory-agent
cp .env.example .env   # QWEN_API_KEY 입력
./install.sh           # uv sync + qmem install (idempotent)
```

제거: `qmem uninstall` (또는 `./uninstall.sh`). 메모리 완전삭제는 `rm -rf ~/.qmem`.

데몬은 `127.0.0.1:8787`, 루트 메모리는 `~/.qmem/mem.db`. 이후 모든 Claude Code 세션에서
SessionStart/UserPromptSubmit 시 관련 교정이 자동 주입되고, PreCompact 시 실수가 수확·검증된다.
LLM 키는 `~/.qmem/.env`(`QWEN_API_KEY`)에서 로드한다(레포 개발 시 레포 `.env`도 폴백). 현재 macOS/launchd 기준.

### 개발 / 테스트

```bash
uv sync && uv run pytest      # 52 tests (Seam1 데몬 HTTP API + Seam2 어댑터 contract)
uv run python demo/run_demo.py   # 오프라인 크로스세션 데모 (네트워크 0)
```
릴리스: `pyproject.toml` 버전 올리고 `git tag vX.Y.Z && git push origin vX.Y.Z` → GitHub Actions(OIDC)가 PyPI 발행.

---

## 데모 시나리오

1. **세션 1 (Claude Code)**: AI가 SQLAlchemy 2.0 async에서 sync Session 사용 → asyncpg
   `another operation in progress` 에러 → compact가 수확 → 설치된 `sqlalchemy==2.x`를 뜯어
   정답(AsyncSession+savepoint) 검증 → **lesson 저장**
2. **재시작(크로스세션) → 세션 2**: 같은 작업 → SessionStart가 lesson 자동 주입 →
   AI가 처음부터 올바르게 → **에러 0**
3. 옛 lesson이 틀린 것으로 판명(또 터짐) → fail++ → confidence 하락 → **stale 도태**
4. confidence 막대 시각화 → "학습 중" 증명

---

## 참고

- omp 메모리 설계: https://github.com/can1357/oh-my-pi/blob/main/docs/memory.md
- Hermes Agent: https://yuv.ai/blog/hermes-agent
- prior art: [claude-mem](https://github.com/thedotmack/claude-mem) · [agentmemory](https://github.com/rohitg00/agentmemory) · [context-mode](https://github.com/mksglu/context-mode) · [ruler](https://github.com/intellectronica/ruler)
- "Hindsight is 20/20" (arxiv 2512.12818): https://arxiv.org/abs/2512.12818
- Qwen Cloud Hackathon: https://qwencloud-hackathon.devpost.com/
