# CONTEXT — Qwen MemoryAgent

이 문서는 아키텍처 정본(source of truth)이자 도메인 용어집(ubiquitous language)이다.
설계 결정의 배경은 `docs/adr/` 참고.

---

## 한 줄 정의

코딩 에이전트의 **낡은 학습지식 + 웹서치 미동봉**으로 생기는 라이브러리/API 실수를,
**compact 시점에 수확 → 디스크의 실제 설치버전으로 검증 → 루트 메모리에 저장 →
다음 어떤 플랫폼의 어떤 세션이든 세션당 1회 자동 주입**하고,
결과로 **스스로 점수를 교정(자가 발전)**하는 host-agnostic 로컬 메모리 데몬.

효용: *"네 코딩 에이전트는 웹서치를 안 해서 낡은 API로 틀린다. 이 메모리는 그 실수를
한 번 잡아 정답을 확인해두고, 모든 미래 세션에 자동 주입한다. 틀리면 스스로 도태시킨다."*

---

## 도메인 용어 (ubiquitous language)

| 용어 | 정의 |
|---|---|
| **Lesson** | 검증된 교정 1건. `{trigger, wrong, right, snippet, source, scope, confidence, use/success/fail, stale}` |
| **Trigger** | lesson 매칭 키 = `패키지@버전 + 작업유형` (예: `sqlalchemy==2.0.31 \| async test`) |
| **Harvest** | PreCompact 시 transcript+에러로그를 스캔해 "사용법 실수 후보"를 뽑는 단계 |
| **Verify** | 후보의 정답을 확정하는 단계. A=설치패키지 뜯기(우선), B=웹서치(폴백) |
| **Inject** | 미래 세션에 lesson을 컨텍스트로 끼워넣음. 호스트 LLM의 도구호출 없이(무개입) |
| **Reflect** | 주입 결과(성공/실패) 신호로 confidence/score를 갱신, 틀린 lesson 도태 |
| **Root memory** | 크로스세션·크로스플랫폼 공용 저장소(`~/.qmem/mem.db`) |
| **Adapter** | 플랫폼별 얇은 훅 스크립트. 이벤트를 데몬에 POST, 주입 컨텍스트를 stdout |
| **Daemon** | 항상 실행되는 두뇌. 저장/회상/수확/검증/reflect 담당 |
| **Tier** | 플랫폼의 통합 가능 등급. 1=훅(풀루프) / 2=MCP / 3=룰파일 |
| **Provider** | LLM 백엔드. OpenAI 호환 추상화, Qwen이 기본값 |

회상 점수: `score = confidence × recency_decay(last_used) × (success+1)/(success+fail+2)`
(reliability는 Beta(1,1) 평활 — 신규 0.5, 성공↑/실패↓. 원식 `success/(s+f+1)`은 신규=0 퇴화가 있어 보정.)

---

## 시스템 토폴로지

```
HOSTS (결정은 얘들이, 메모리에 무개입)
  Claude Code[레퍼런스] · Codex · Gemini CLI · Cursor · ...
       │ 라이프사이클 훅 (stdin: event+transcript_path / stdout: 주입ctx)
  ┌────▼──────────────────────────────────────┐
  │ ADAPTER LAYER  플랫폼별 얇은 훅 스크립트       │
  └────────────────┬───────────────────────────┘
                   │ HTTP localhost  fire-and-forget
  ┌────────────────▼───────────────────────────────────────────┐
  │ LOCAL DAEMON                                                │
  │  Ingress · Recall(inject) · Harvest(compact) · Reflect      │
  │  ┌───────────────────────────────────────────────────────┐ │
  │  │ MEMORY STORE  SQLite+FTS5  ~/.qmem/mem.db              │ │
  │  │ L1 Curated(항상주입,~2k) · L2 Episodic(원문,FTS5) ·     │ │
  │  │ L3 Scored(lesson 본체, rerank top-K 주입)              │ │
  │  └───────────────────────────────────────────────────────┘ │
  │  Verifier(A:패키지뜯 / B:웹서치) · LLM Provider(Qwen기본)    │
  └──────┬───────────────────────────────┬─────────────────────┘
         │ DISK                          │ LLM ENDPOINT (OpenAI 호환)
   node_modules/ site-packages/    qwen-turbo(추출) · qwen-plus(검증/합성,+search)
   (실제 설치버전 = 정답 출처)        · qwen3-rerank(회상)  | 교체: OpenAI/로컬
```

---

## 5단계 파이프라인 (lesson의 생애)

```
①HARVEST   PreCompact 훅 → transcript + 세션중 에러로그
           → qwen-turbo가 "사용법 실수 후보" 추출 (에러신호로 후보 좁힘) [async]
②VERIFY    A. 설치패키지 뜯기(버전·타입·README) ◄우선
           B. 없으면 웹서치(qwen-plus enable_search) 폴백
           → qwen-plus가 "버전-정확 권장법"=lesson 합성 [async]
③STORE     lesson 레코드 + FTS5 인덱싱 + 모순체크(충돌→옛것 stale)
④INJECT    SessionStart: 매니페스트(package.json/requirements.txt) 읽어 프리로드
           UserPromptSubmit: 기술언급 감지→주입
           세션당 보증: injected={session_id: set(lesson_id)} 로 (세션,lesson) 1회
           → additionalContext stdout → 호스트가 모델 컨텍스트에 삽입 (LLM 무개입)
⑤REFLECT   결과신호(테스트통과/에러0=success / 또터짐·유저교정=fail)
           → score 갱신 → 낮으면 archive(도태), 높으면 우선주입 ↺①
```

약한 고리: **결과 귀속(outcome attribution)** 은 상관에 근사 — 인과 보장 X.
양이 쌓이면 통계적으로 수렴. 데모는 "테스트 통과/실패 → confidence 막대"로 증명.

---

## 멀티플랫폼 통합 — 3등급

감지는 쉬움(설정경로 `exists` 루프). 변수는 통합 가능 등급:

```
TIER 1 훅   → 풀루프(자동주입+compact수확)  ★타겟
            Claude Code · Gemini CLI · Cursor · Copilot CLI · Kiro · (Qwen Code)
TIER 2 MCP  → recall을 MCP 툴 노출(호스트가 호출, 반쪽)
            VS Code Copilot · Zed · OpenCode · Kilo · Kimi · JetBrains · Antigravity
TIER 3 룰   → AGENTS.md 정적 포인터만(동적주입 X, 최소)
            Aider · Cline · Goose · Warp · Windsurf
```

감지 레지스트리(데이터로 분리, 새 플랫폼=표 한 줄):

| 플랫폼 | 감지 경로 | tier |
|---|---|---|
| Claude Code | `~/.claude/settings.json` | hooks |
| Qwen Code | `~/.qwen/settings.json` | hooks |
| Gemini CLI | `~/.gemini/settings.json` | hooks |
| Codex | `~/.codex/config.toml` | mcp(훅 신규) |
| Cursor | `~/.cursor/hooks.json`, `~/.cursor/mcp.json` | hooks |
| Copilot CLI | `~/.copilot/hooks/` | hooks(precompact X) |
| Zed | `~/.config/zed/settings.json` | mcp |
| Aider | `AGENTS.md` | rules |

---

## 설치기 (코어 이후 단계)

```
$ uvx qwen-memory init
 STEP1 SCAN     레지스트리 감지경로 exists 루프 → detected
 STEP2 PRESENT  감지된 것만 체크박스(기본 전체ON), tier 표기(거짓약속 금지)
 STEP3 WIRE     선택 플랫폼에 등급별 와이어링
                tier1→settings/hooks.json에 훅 등록
                tier2→mcp.json에 qmem MCP 등록
                tier3→AGENTS.md에 참조 블록 append
 STEP4 DAEMON   ~/.qmem 생성, mem.db 초기화, 데몬 등록/기동
```

---

## 차별점 (vs prior art)

claude-mem · agentmemory · context-mode 는 "대화를 압축 저장/주입"까지만 한다.
본 프로젝트의 wedge:
1. **설치된 패키지를 직접 뜯어 버전-정확하게 검증** (낡음·환각 0, 오프라인)
2. **점수형 Reflect로 자가 교정** (틀린 lesson 자동 도태 = "increasingly accurate")

플러밍(훅·자동감지·멀티플랫폼)은 prior art 패턴을 그대로 차용하고,
시간은 위 두 wedge에 집중한다.

---

## 기술 스택 (권장)

```
언어     Python 3.12          데몬   FastAPI + uvicorn (async)
저장     sqlite3 + FTS5       LLM    openai SDK (base_url 교체)
기본모델  qwen-turbo/plus/qwen3-rerank (dashscope-intl)
검증     importlib.metadata / node_modules 파서 · enable_search(폴백)
설치기   uvx qwen-memory init (npx 래퍼 가능)
```
```

scoring:  score = confidence × recency_decay × (success+1)/(success+fail+2)
```
