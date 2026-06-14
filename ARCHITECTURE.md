# 🏗️ Science AI Lab — 구현 원리와 아키텍처

이 문서는 시스템이 **어떻게, 어떤 방식으로 동작하는지** 코드 흐름 중심으로 설명합니다.
(파일 경로는 `backend/`·`frontend/` 기준)

---

## 0. 한눈에 보는 전체 그림

```
                    ┌──────────────── 라즈베리파이 5 (1대 = 1모둠) ────────────────┐
                    │                                                             │
  [ESP8266 + 센서] ─┼─MQTT─▶ Mosquitto ─▶ mqtt_client ─┐                          │
   (모둠당 1~3대)    │                                  │                          │
                    │                                  ▼                          │
  [학생 화면]  ◀─WS──┼── ws_hub ◀── sensor_rule_engine ─┤  (룰 매칭 → 즉답)         │
  Chromium 키오스크  │      ▲                            │                          │
        │           │      │                            ▼                          │
        └─HTTP/SSE──┼─▶ FastAPI ─▶ response_router ─┬─▶ 스크립트(0ms)             │
                    │   (main.py)                   ├─▶ 룰(sensor_rule_engine)    │
                    │                               └─▶ LLM ─▶ Ollama(gemma3)     │
                    │                                         ▲                    │
                    │   SQLite(lab.db) ◀── 모든 상태/메시지    │ RAG(과거 사례)      │
                    │   nomic-embed-text ─▶ vector_store ─────┘                    │
                    └─────────────────────────────────────────────────────────────┘
                         모든 것이 로컬 · 인터넷 불필요 · 데이터는 SSD(/mnt/nvme)
```

핵심 설계 한 줄: **"결정적인 것은 코드(스크립트·룰)로 0ms에, 창의적인 것만 LLM으로."**

---

## 1. 요청 한 번이 흐르는 길 (가장 중요)

학생이 무언가 입력하면 `POST /api/chat`(`routers/chat.py`)로 들어와 **응답 라우터**(`services/response_router.py`)가 **누가 답할지**를 먼저 결정합니다. 이게 시스템의 심장입니다.

```
학생 입력 → /api/chat → response_router.route(input_type, payload, session)
                              │
        ┌─────────────────────┼──────────────────────────┐
   input_type=="quick_reply"  input_type=="text"     input_type=="sensor"
        │                     │                          │
   버튼 100% 스크립트     intent_classifier.classify()   sensor_rule_engine.evaluate()
   step.scripted_replies      │                          │
   [button_id] 즉답      ┌────┼─────┬──────┬────────┐     ├ 임계값 매칭 → 스크립트(rule)
                      confirm deny repeat danger question  ├ 정상범위 → 5초당 1회 격려
                         │    │    │     │       │         └ 그 외 → 무응답(silent)
                      스크립트 즉답 ───────┘    LLM 호출
                                                  │
                                          prompt_builder.build_system_prompt()
                                          (+진화 addon +RAG 컨텍스트)
                                                  │
                                          Ollama /api/generate (스트리밍)
```

### 반환 형태 (decision)
`route()`는 실행이 아니라 **결정**만 돌려줍니다:
```python
{ "source": "scripted"|"rule"|"llm"|"none",
  "content": "즉답 텍스트"|None,   # 스크립트/룰일 때
  "script_id": "step.scripted_replies.done"|...,  # 분석용
  "system_prompt": "..." }          # llm일 때만
```
`chat.py`가 이 결정을 보고:
- `scripted`/`rule` → **SSE 단일 메시지**로 즉시 전송 (지연 ~0ms)
- `llm` → `thinking` 이벤트 후 **토큰 스트리밍**
- `none` → `silent` (조용히 무응답 — 센서값이 정상이고 변화 없을 때)

모든 assistant 메시지는 `messages` 테이블에 `response_source`/`script_id`/`latency_ms`와 함께 기록되어, `/api/stats/routing`이 **스크립트 vs LLM 비율**을 실측합니다(목표 70~85% 스크립트).

### 왜 이렇게?
- **속도**: 버튼·단계 안내·정상범위 격려는 매번 같은 문장 → LLM(2~3초) 대신 코드(0ms)
- **안전**: 위험어("불"·"콘센트")는 LLM을 절대 거치지 않고 `intent_classifier`가 `danger`로 잡아 **고정 경고 스크립트** 반환 (환각 차단)
- **발열·전력**: Pi에서 LLM 호출이 줄어 CPU 부하·온도 ↓

---

## 2. 의도 분류 (`services/intent_classifier.py`)

머신러닝 없이 **정규식 + 키워드 사전**으로 5가지로 분류합니다. "확실한 것만 스크립트, 애매하면 LLM"이 원칙이라 미분류는 무조건 `question`(→LLM).

| 의도 | 예 | 처리 |
|---|---|---|
| `danger` | "불", "콘센트", "감전" | **최우선** → 고정 경고 스크립트 |
| `confirm` | "응", "네", "다음" | 스크립트(다음 단계) |
| `deny` | "아니", "싫어" | 스크립트(격려) |
| `repeat` | "다시", "몰라" | 스크립트(단계 재안내) |
| `question` | "왜~", "어떻게~", 그 외 전부 | **LLM** |

위험어를 1순위로 검사하는 게 안전 설계의 핵심입니다.

---

## 3. 센서 룰 엔진 (`services/sensor_rule_engine.py`)

`experiments.json`의 각 단계(step)에 들어 있는 `sensor_thresholds`를 평가합니다.

```json
"sensor_thresholds": {
  "temperature": [
    { "range": "> 5",    "scripted": "아직 차가워지는 중이야 🥶" },
    { "range": "0 ~ 5",  "scripted": "이제 곧 얼겠다! 👀" },
    { "range": "< 0",    "scripted": "와! 얼음이 되고 있어 ❄️" }
  ]
}
```
지원 문법: `> 5`, `>= 20`, `< 0`, `0 ~ 5`(구간), `== 1`(불리언), `dry`/`wet`(의미 토큰).
매칭되면 **정해진 멘트(rule)**를 즉시 반환 → LLM보다 항상 먼저. 매칭이 없고 값이 정상이면 5초당 1회 격려(배열에서 직전 것 제외 랜덤 → 같은 말 반복 방지).

---

## 4. 데이터 = 단일 진실 소스 (`backend/data/*.json`)

LLM 프롬프트·챗봇·추천·시각화·RAG가 **모두 같은 JSON**을 봅니다. `services/data_loader.py`가 부팅 시 로드하고 **Pydantic으로 스키마 검증 + 상호참조 검증**(실험이 참조하는 센서/단원이 실제 존재하는가)을 수행합니다.

| 파일 | 내용 | 검증 |
|---|---|---|
| `sensors.json` | 센서 40종 (핀·라이브러리·안전·학생힌트·교사노트) | 필드/타입 |
| `curriculum.json` | 2022 개정 3~6학년 단원 32개 | 성취기준 플래그 |
| `experiments.json` | 실험 14개 (단계·코칭·임계값·스크립트) | 센서/단원 교차참조 |
| `onboarding.json` | 45분 첫 수업 6단계 | — |
| `dialogue_templates.json` | 전역 스크립트(인사·전환·안전·격려·에러) | — |
| `node_explanations.json` | 노드 설명(학년별) | — |

`GET /api/data/validate`가 무결성 리포트(항목 수·학년별 실험·미사용 센서·오류/경고)를 돌려줍니다. **데이터를 고치는 것이 곧 시스템을 고치는 것** — 교사가 JSON만 편집해도 동작이 바뀝니다.

---

## 5. 시스템 프롬프트 조립 (`services/prompt_builder.py`)

LLM은 "자유 질문(20%)"만 담당하므로, 프롬프트에 **맥락을 주입**하고 안전·역할을 못박습니다:
- 학년 → 응답 길이/어휘 (3~4학년 2문장, 5~6학년 4문장)
- 현재 실험·단계·사용 센서·코칭 방향
- "지시 말고 질문으로", "안전 질문엔 직접 답 말고 선생님과 함께"
- **(Phase 7)** 진화된 addon(교사 큐레이션 학습) + RAG 과거 사례

---

## 6. 실시간 센서 파이프라인 (Phase 4)

```
ESP8266 ─MQTT(science-lab/sensors/{id}/data/{sensor})─▶ Mosquitto
                                                          │
                                  services/mqtt_client.py (paho, 백그라운드 스레드)
                                                          │
        ┌──────────────┬──────────────┬──────────────────┼───────────────┐
        ▼              ▼              ▼                  ▼               ▼
 sensor_registry  data_buffer   sensor_readings    sensor_rule_engine  flow_state
 (생존 15s timeout) (60초 deque)  (DB 시계열)        (룰→챗 rule 메시지)  (노드 펄스)
        │              │                                 │               │
        └──────────────┴─────────── ws_hub.publish() ────┴───────────────┘
                                       │
                       ws_hub: 스레드→asyncio 안전 전달 (call_soon_threadsafe)
                                       │
                      /ws/sensors (학생 위젯) · /api/flow/ws (노드 다이어그램)
```

**스레드 경계 처리**가 핵심입니다. paho-mqtt는 별도 스레드에서 콜백이 돌고, FastAPI WebSocket은 asyncio 루프에 있습니다. `services/ws_hub.py`가 `loop.call_soon_threadsafe`로 두 세계를 안전하게 잇습니다.

ESP 펌웨어(`esp8266/template.ino`)는 **결정적 템플릿**입니다 — `#define ESP_ID`, `#define SENSOR_INCLUDE` 두 줄만 바꿔 굽고, LLM이 코드를 생성하지 않습니다(안전·재현성). 센서별 동작은 `esp8266/sensors/*.h` 10종이 `read_sensor()` 인터페이스로 제공합니다.

---

## 7. 노드 시각화 (Phase 5, `frontend/flow.html`)

데이터 1건이 도착하면 `flow_state.pulse_chain()`이 `[sensor→esp→mqtt→graph(→ai)]` 순서와 펄스 시간을 `/api/flow/ws`로 보냅니다. 프론트는 **상태만 받아** 자체 SVG + CSS 애니메이션으로 노드를 깜빡이고 데이터 입자를 선 따라 이동시킵니다. (React Flow/vis.js 대신 자체 SVG — Pi 경량) 룰이 매칭됐을 때만 AI 노드까지 펄스가 이어집니다.

---

## 8. 차시 이어하기 & 리플레이 (Phase 5)

- **체크포인트** (`services/checkpoint.py`): 단계 변경·안전수칙·도움요청·주기적으로 자동 저장. 측정요약은 **저장 시점이 아니라 조회 시점에 readings로 재계산**(손실 0). 부팅 시 미완료 세션을 감지해 "이어할까?"를 띄우고, 이어할 때 안전수칙을 간소 재복창.
- **리플레이** (`services/replay.py`): 종료 세션의 `messages`+`sensor_readings`를 시간순 병합해 `/api/replay/{id}/stream`이 **SSE로 배속 재생**(빈 구간은 점프). 교사 도구.

---

## 9. 재귀적 자기발전 (Phase 7)

```
수업 → LLM 답변 → anomaly_detector(위험/회피/미보유/길이) → 이상 시 curation_queue 적재
                                                                  │
교사 /curation 페이지 → ✓승인 / ✗거부 / ✏수정                      │
        │                                                         │
        ├─ 승인/수정 → embeddings(nomic-embed-text) → vector_store(approved 태그)
        │
        └─ prompt_evolver.evolve() → 좋은/피할 패턴 추출 → prompt_versions(버전·롤백)
                                          │
                            prompt_builder가 active addon 주입

다음 학생 질문 → rag.retrieve() → vector_store.search()
                  (코사인 유사도, 같은 학년/단원 가중, approved ×2)
                  → top-3 과거 사례를 프롬프트 컨텍스트로
```

**벡터 검색은 sqlite-vss 대신 numpy 코사인 brute-force**(`services/vector_store.py`)로 구현했습니다 — aarch64(Pi)에서 sqlite-vss 빌드가 불안정하고, 교실 데이터 규모(수천 건)에선 충분히 빠르기 때문입니다. 인터페이스는 동일해 나중에 교체 가능합니다.

원칙: **시스템 진화는 100% 교사 큐레이션 의존**(자동 학습 X), 모든 프롬프트 변경은 버전 기록·롤백 가능, 환각 탐지는 알림만(교사 결정 최종), 학생 식별정보는 영구 저장 안 함(`anonymizer.py`, 세션 종료 시 별명 NULL).

---

## 10. 안전·개인정보 설계

- **안전 메시지는 LLM 절대 불신** → 항상 스크립트(`dialogue_templates.json`의 고정 문구). 실험 전 안전수칙 복창 게이트(`safety_ritual.py`)를 통과해야 시작.
- **위험 키워드**는 의도 분류 1순위로 차단.
- **개인정보**: 별명·역할은 세션 종료 시 자동 NULL. 음성·사진·IP·MAC은 저장 안 함. 학년·단원·측정값·질문/답변만 익명으로 보관.
- **1 Pi = 1 모둠**: 새 세션 시작 시 이전 active 세션 자동 종료(단일 활성 보장). Pi 한 대가 죽어도 다른 모둠 무관.

---

## 11. 데스크톱 통합 & 자가치유 (Phase 6)

```
전원 ON → systemd(부팅)
  ├ mosquitto.service / ollama.service
  ├ science-ai-backend.service   (FastAPI, Restart=on-failure)
  ├ science-ai-warmup.service    (gemma3:1b 첫 응답 워밍)
  ├ science-ai-watchdog.service  (5분 헬스체크, 3회 실패 시 재시작)
  └ science-ai-ap.service        (WiFi AP, 선택)
       ↓
  바탕화면 [과학 실험실] 아이콘 → launcher.sh
       ↓
  백엔드 헬스체크 → Ollama 워밍 → 미완료 세션이면 ?resume=1
       ↓
  Chromium --kiosk --app=http://localhost:8000
```

- **학생 보호** (`frontend/student_lock.js`): 키오스크 + F11/F12/우클릭/새로고침/탭이동 차단. 교사 PIN 입력 시 해제, 30초 무입력 시 자동 재잠금.
- **워치독 자동복구**: 백엔드가 죽으면 워치독이 `systemctl restart`(NOPASSWD 제한 등록)로 5분 내 복구.
- **진단** (`/api/admin/diagnose`): Ollama·MQTT·디스크·메모리·온도·경고를 한 화면에.
- **배포**: `install.sh`(설치) / `update.sh` / `backup.sh`(cron) / `restore.sh` / `clone-to-new-pi.sh`(새 모둠 30분) / `first_boot.py`(모둠·PIN 설정).

---

## 12. 기술 선택 이유 요약

| 선택 | 이유 |
|---|---|
| 스크립트 80% + LLM 20% | 속도·일관성·안전·발열. 결정적 응답에 LLM은 과함 |
| Ollama 로컬 LLM | 인터넷 없는 교실, 학생 데이터 외부 유출 0 |
| 자체 SVG (노드/그래프) | React Flow/vis.js는 Pi에 무거움 |
| numpy 코사인 (벡터) | aarch64 sqlite-vss 빌드 불안정, 데이터 규모 작음 |
| 결정적 ESP 펌웨어 | LLM 코드 생성은 안전·재현성 위험 |
| 모든 데이터 SSD | SD 카드 쓰기 수명 보호 (부팅만 SD) |
| 1 Pi = 1 모둠 | 멀티테넌트 복잡도 제거, 장애 격리 |

---

> 더 깊은 내용은 각 `backend/services/*.py` 상단 docstring에 모듈별로 정리되어 있습니다.
> 진행 기록은 [`PLANNING.md`](PLANNING.md), 설치는 [`INSTALL.md`](INSTALL.md) 참고.
