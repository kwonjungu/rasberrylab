# 🧪 Science AI Lab

**로컬 LLM 기반 초등 과학 실험 AI 플랫폼** — 라즈베리파이 한 대가 한 모둠(4명)의 과학 실험 친구가 됩니다.

> 경기교육청 소속 초등 교사가 만드는, 2022 개정 초등 과학 교육과정에 매핑된 인터넷 없는 교실용 AI 실험 도우미.

---

## 의도 (왜 만드는가)

초등학생이 **AI와 대화하며 직접 센서로 실험**하고, 그 과정이 실시간 노드 다이어그램으로 시각화되는 시스템입니다. 핵심 설계 원칙은 다음과 같습니다.

- **🏫 인터넷 없는 교실에서 동작** — 모든 처리(LLM·MQTT·DB)가 라즈베리파이 안에서 일어납니다. 클라우드·외부 API 의존 없음. 학생 데이터가 교실 밖으로 나가지 않습니다.
- **👦 초등학생 눈높이** — 큰 폰트(1m 거리 가독성), 직관적 아이콘, TTS 음성 안내, 학년별 어휘·UI 자동 조절. 에러 메시지도 학생이 이해할 한국어로.
- **⚡ 스크립트 80% + LLM 20% 하이브리드** — 결정적 응답(버튼·단계 안내·안전 수칙·정상 범위 격려)은 **스크립트로 0ms 즉답**, 자유 질문·이상값 해석만 LLM이 담당. 체감 속도 ↑, Pi 발열 ↓, 안전 메시지 100% 일관성, 환각 위험 최소화.
- **🛡️ 안전 우선** — 안전 관련 응답은 LLM을 절대 신뢰하지 않고 **무조건 스크립트**. 실험 전 안전 수칙 복창 게이트, 위험 키워드("불"·"콘센트") 즉시 차단.
- **🔒 개인정보 보호** — 학생 별명·역할은 세션 종료 시 자동 삭제(NULL). 영구 저장 안 함.
- **📦 1 Pi = 1 모둠** — 멀티테넌트·중앙 콘솔 없음. Pi 한 대가 죽어도 다른 모둠에 영향 없음. SD는 부팅 전용, 모든 데이터·로그·DB는 SSD(`/mnt/nvme`)에 두어 SD 카드를 보호.
- **♻️ 재귀적 자기 발전** — 세션 저장 → RAG → 교사 큐레이션 → 시스템 프롬프트 진화(예정).

---

## 하드웨어

- **Raspberry Pi 5 (8GB)**, Debian 13 (trixie) — 부팅은 SD, 모든 작업/데이터는 NVMe SSD
- **ESP8266** 보드 다수 (모둠당 1~3대)
- **KEYES 37-in-1 센서 키트** + HC-SR04 초음파 + DC 모터(+드라이버)

## 기술 스택

| 영역 | 기술 |
|---|---|
| LLM | Ollama (`gemma3:1b` 빠른 채팅 / `gemma3:4b` 품질) — 전부 로컬 |
| 백엔드 | FastAPI (Python 3.13), SQLite |
| 프론트 | Vanilla HTML + Alpine.js + 자체 SVG (React Flow/vis.js 미사용 — Pi 경량) |
| 실시간 | Mosquitto MQTT + WebSocket |
| 펌웨어 | ESP8266 (결정적 템플릿 + 센서 헤더, LLM 코드 생성 안 함) |

---

## 진행 현황 (Phase)

- [x] **Phase 1 — 기반**: SSD 바인드 마운트, Ollama·Mosquitto, FastAPI 스켈레톤
- [x] **Phase 2 — 데이터**: 센서 40종 + 단원 32개 + 온보딩 + 실험 14개 (무결성 검증 통과)
- [x] **Phase 3 — 챗 UI + 응답 라우팅**: 스크립트/룰/LLM 하이브리드, 학년별 UI, 안전 수칙, 역할 카드, 도움요청(GPIO), 교사 모드(PIN), PDF 활동지
- [x] **Phase 4 — ESP8266 + MQTT**: 실시간 센서 수신·룰 트리거·WebSocket 푸시, 펌웨어 템플릿 + 센서 헤더 10종
- [x] **Phase 5 — 노드 시각화 + 이어하기 + 리플레이**: 데이터 흐름 다이어그램, 차시 이어하기 체크포인트, 세션 리플레이
- [x] **Phase 6 — 데스크톱 통합**: 자동 기동(systemd 4종), 키오스크 런처·워치독, 배포 스크립트(install/update/backup/restore/clone), 학생 보호(키 차단·교사 PIN), 진단 API — 적용은 콘솔(`INSTALL.md`)
- [x] **Phase 7 — 재귀 학습**: 임베딩(nomic-embed-text)·벡터 검색(numpy 코사인)·RAG·교사 큐레이션·환각 자동 분류·시스템 프롬프트 진화(버전·롤백)·익명화·학급 분석 대시보드

---

## 폴더 구조

```
science-ai/
├── backend/
│   ├── main.py                 # FastAPI 엔트리 (lifespan: DB·데이터·MQTT 기동)
│   ├── routers/                # data, chat(SSE), session, teacher, stats,
│   │                           #   sensors(+WS), flow(+WS), checkpoint, replay
│   ├── services/               # response_router ⭐, intent_classifier,
│   │                           #   sensor_rule_engine, prompt_builder, mqtt_client,
│   │                           #   sensor_registry, data_buffer, ws_hub, flow_state,
│   │                           #   checkpoint, replay, report_pdf, db, schemas
│   ├── data/                   # sensors/experiments/curriculum/onboarding/
│   │                           #   dialogue_templates/node_explanations .json (단일 진실 소스)
│   └── assets/fonts/           # NanumGothic (PDF 한글, 오프라인)
├── frontend/                   # index.html, app.js, chat.js, flow.html, style.css, lib/(로컬)
├── esp8266/                    # template.ino + sensors/*.h(10종) + flash_script.sh
├── network/                    # hostapd/dnsmasq/mosquitto-lan 설정 (콘솔 적용)
└── db/                         # schema.sql, lab.db(런타임), reports/(PDF)
```

## 실행

```bash
cd backend
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000
# → http://localhost:8000  (학생 화면)
# → http://localhost:8000/flow.html  (노드 다이어그램, 빔프로젝터용)
```

전제: 같은 Pi에 Ollama(`gemma3:1b`, `gemma3:4b`)와 Mosquitto가 동작 중이어야 합니다.

---

## 📖 구현 원리

**어떻게·어떤 방식으로 동작하는지**는 [`ARCHITECTURE.md`](ARCHITECTURE.md)에 코드 흐름 중심으로 자세히 정리했습니다:
- 요청 한 번이 흐르는 길 (응답 라우터 = 시스템의 심장)
- 스크립트/룰/LLM 분기, 의도 분류, 센서 룰 엔진
- 실시간 MQTT 파이프라인 (스레드↔asyncio 경계 처리)
- 노드 시각화, 차시 이어하기/리플레이
- RAG·교사 큐레이션·프롬프트 진화
- 자동 기동·자가치유·학생 보호
- 기술 선택 이유 요약

진행 기록은 [`PLANNING.md`](PLANNING.md), 설치·운영은 [`INSTALL.md`](INSTALL.md) 참고.

## 라이선스 / 기여

경기교육청 초등 과학 교육용 프로젝트. 교실 환경(인터넷 없음·초등학생·안전)을 1순위로 설계합니다.
