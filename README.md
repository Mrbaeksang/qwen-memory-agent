# Qwen MemoryAgent

> **Global AI Hackathon Series with Qwen Cloud — Track 1: MemoryAgent**
> 쓸수록 정확해지는(self-improving) 영속 메모리 에이전트. Qwen Cloud 기반.

지속적으로 경험을 축적하고, 사용자 선호를 기억하며, 멀티턴·크로스세션에서 **점점 더 정확한 결정**을 내리는 에이전트. 핵심은 단순 저장이 아니라 **(1) 효율적 저장/검색 · (2) 오래된 정보의 적시 망각 · (3) 제한된 컨텍스트 안에서 핵심 회상**이다.

---

## 핵심 아이디어

오픈소스 에이전트 메모리 설계(omp, Hermes Agent)에서 검증된 부분만 추출하고, 여기에 **점수 기반 Reflect 루프**를 더해 "쓸수록 정확해지는" 성질을 코드로 구현한다.

| 출처 | 가져온 것 |
|---|---|
| **omp (Oh My Pi)** | 2단계 파이프라인(세션별 추출 → 크로스세션 통합), 모순=stale 망각, 토큰캡 주입 |
| **Hermes Agent** | 3층 메모리, FTS5 세션검색(임베딩 0원), 백그라운드 리뷰 nudge 루프, 스킬화 |
| **본 프로젝트** | 점수형 메모리 + Reflect (success/fail → confidence 갱신, lesson 작성) |

---

## 아키텍처

### 메모리 3층
```
L1 Curated (항상 주입)   : 사실·선호·관례, 하드 토큰캡 ~2k
L2 Episodic (검색)       : SQLite + FTS5, 원문 턴 저장 (임베딩 비용 0)
L3 Scored (랭킹 회상)    : 사실 + confidence 점수, top-K만 회상
```

### 3개의 루프
```
① 인라인(매 턴)   : L1 주입 + (FTS5 + score) top-K 회상 → Qwen 결정
② 백그라운드 리뷰 : N턴마다 async 포크가 추출·통합·stale 폐기 (유저 응답 비차단)
③ Reflect(결과시) : 성공→confidence↑ / 실패→confidence↓ + lesson 작성
```

### 망각 3트리거
- **모순** → stale 처리
- **나이/미사용** → confidence 감쇠 후 archive
- **용량 초과** → 강제 통합/압축

### 메모리 스키마
```python
Memory = {
  "content": "...",                  # 사실 / 선호 / 교훈(lesson)
  "type": "fact | preference | lesson | skill",
  "confidence": 0.7,
  "use_count": 0,
  "success_count": 0,                # 이 기억을 쓴 결정이 성공한 횟수
  "fail_count": 0,
  "created_at": ..., "last_used": ...,
}

score = confidence × recency_decay(last_used) × success/(success+fail+1)
```

---

## 심사 기준 매핑

| 심사 기준 | 구현 |
|---|---|
| ① 효율 저장/검색 | L2 FTS5(임베딩 0) + L3 점수 랭킹 |
| ② 적시 망각 | 모순 stale + 감쇠 + 용량 통합 (3트리거) |
| ③ 제한 컨텍스트 회상 | L1 토큰캡 + top-K만 주입 |
| **increasingly accurate** | Reflect의 success/fail 점수 갱신 + lesson |

---

## Qwen 모델 배분 (토큰 예산 방어)

| 용도 | 모델 |
|---|---|
| 인라인 결정 | `qwen-plus` |
| 백그라운드 추출/통합 | `qwen-turbo` |
| L2 키워드 검색 | LLM 미사용 (FTS5) |

**API**: OpenAI 호환 — `base_url=https://dashscope-intl.aliyuncs.com/compatible-mode/v1`

---

## 빌드 단계

- [ ] **P1** — SQLite + FTS5 스키마, 메모리 CRUD/검색 (L2)
- [ ] **P2** — 인라인 회상 → Qwen 결정 루프 (L1 토큰캡 주입)
- [ ] **P3** — 백그라운드 리뷰 nudge (추출 → 통합 → stale)
- [ ] **P4** — Reflect 점수 루프 + lesson 작성 *(차별화 핵심)*
- [ ] **P5** — 데모 시나리오 + confidence 점수 시각화

---

## 데모 시나리오

1. **세션 1**: 틀린 결정 → 유저 교정 → 백그라운드 nudge가 **lesson 저장**
2. **재시작(크로스세션)** → **세션 2**: 같은 상황 → lesson 회상 → **이번엔 맞게 결정**
3. 옛 정보 주입 → 에이전트 **"stale라 버림"**
4. confidence 점수 막대 시각화 → "학습 중" 증명

---

## 참고

- omp 메모리 설계: https://github.com/can1357/oh-my-pi/blob/main/docs/memory.md
- Hermes Agent: https://yuv.ai/blog/hermes-agent
- "Hindsight is 20/20" (arxiv 2512.12818): https://arxiv.org/abs/2512.12818
- Qwen Cloud Hackathon: https://qwencloud-hackathon.devpost.com/
