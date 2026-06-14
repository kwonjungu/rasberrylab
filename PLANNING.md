# Science AI Lab — 진행 메모

로컬 LLM 기반 초등 과학 실험 AI 플랫폼 (경기교육청, 2022 개정 교육과정)

## 환경 (확정)
- Pi 5 8GB / Debian trixie, 모든 데이터는 `/mnt/nvme` 아래 (SD 보호)
- `/home`, `/var` → SSD 바인드 마운트 완료
- Ollama systemd 자동기동, `OLLAMA_MODELS=/mnt/nvme/ollama`
  - `gemma3:1b` (815MB, ~13 tok/s) — 빠른 채팅
  - `gemma3:4b` (3.3GB, ~3.5 tok/s) — 품질 답변
  - `gemma2:2b`, `qwen2.5:1.5b` (보조)

## 보유 하드웨어
- ESP8266 다수, KEYES 37-in-1 센서 키트, HC-SR04 초음파, DC 모터(+드라이버)

## Phase 진행 상황
- [x] Phase 1: 폴더 구조, FastAPI 스켈레톤(/health, /api/ollama/test), Mosquitto
- [x] Phase 2: 센서40 + 단원32 + 온보딩 + 실험14(시드10 + 제시4: RC카·자동문·자율주행·스마트화분) / 무결성 통과(오류0·경고0)
  - 교사 결정: 모든 단원 커버 X, 제시된 실험만. 미사용 센서 5개(중복/고난도)는 의도된 것
- [~] Phase 3: 챗 UI + **v3.1 응답 라우팅** (스크립트 80% / LLM 20%) — 1 Pi = 1 모둠(4명) 한 화면
  - [x] Day 1: DB(sessions/messages/runs/badges) · dialogue_templates.json · intent_classifier(10/10) · sensor_rule_engine · response_router · /api/session/* · /api/chat(SSE) · /api/stats/routing — 스크립트/룰/LLM 3경로 동작 확인
  - [x] Day 2: 단일 화면(index.html/app.js/chat.js/panel.js/style.css), 라이브러리 로컬(alpine/marked), 빠른답변 즉답, TTS(Web Speech), 학년별 UI(gradeTier), 모드전환(greeting→onboarding 6단계/experiment), /api/session/{id}/current, static 마운트
  - [x] Day 3: 시드10 보강(22 step + 측정step 임계값) · safety_ritual(복창 게이트) · role_manager(4역할 카드) · help_signal(GPIO18 부저/23 LED, gpiozero 폴백→화면깜빡임) · 막힘신호(stuck 2회→도움권유) · 엔드포인트(roles/safety/help)+프론트 연동
    - ⚠️ GPIO 실동작은 gpiozero 설치 + 부저/LED 배선 후 Pi에서 확인 필요(현재 폴백 동작 검증됨)
  - [x] Day 4: 교사모드(PIN/뷰/제어/주입, 30초 자동복귀) · report_pdf.py(matplotlib 그래프+LLM 결론+reportlab, 나눔고딕 번들) · sensor_readings 저장 · /end→PDF생성·서빙 · 시나리오 완주 검증
    - /api/stats/routing 동작(합성 테스트 93% 스크립트 — 실수업서 자유질문 늘면 15~30% LLM 대역). PDF 74KB 생성·HTTP200
- [x] Phase 4: ESP8266 + MQTT + 실시간 (소프트웨어 완료)
  - 백엔드: mqtt_client(paho)·sensor_registry·data_buffer·ws_hub·routers/sensors(active/recent/history/command + /ws/sensors). 단일 active 세션 보장
  - 룰 통합: 라이브 센서값 → sensor_rule_engine → 챗에 rule 메시지 + WS 푸시 (가짜 ESP로 검증: temp/distance 트리거 OK, WS data 수신 OK)
  - 펌웨어: template.ino(결정적, #define 2줄) + 센서헤더 10종 + wifi_config.h.example + flash_script.sh
  - 네트워크(준비만, 콘솔 실행): network/{hostapd,dnsmasq,mosquitto-lan}.conf, setup_ap.sh, README
  - 프론트: ESP 상태 위젯(🤖/😵) + sparkline + 라이브 룰 메시지 표시
  - ⚠️ 미적용(콘솔 필요): Pi AP 전환·Mosquitto LAN 리스너·펌웨어 굽기. 미작성: wizard.html(센서연결 마법사)
  - 원칙 준수: 펌웨어=결정적 템플릿, 1 Pi=1 모둠, 로컬 전제, WiFi 비번 학생 비노출
  - 원칙: 결정적 응답(버튼·단계안내·안전수칙·타이머·정상범위 격려)=스크립트(0ms), 자유질문·이상값해석·요약=LLM
  - Phase 3 런타임 산출물(미작성): `services/response_router.py`, `services/intent_classifier.py`(키워드/정규식), `services/sensor_rule_engine.py`, `/api/stats/routing`, DB messages 컬럼(response_source/script_id/latency_ms), `/api/chat` 라우터 통합
  - 안전 메시지는 LLM 절대 불신 → 무조건 스크립트. 격려는 배열에서 직전 것 제외 랜덤. 목표 비율 스크립트 70~85%
  - Phase 2에서 선반영(데이터): experiments step의 `scripted_replies`/`sensor_thresholds`/`llm_trigger_examples`, `data/dialogue_templates.json`
- [ ] Phase 4: ESP8266 + MQTT PoC (DHT11 온도)
  - ⚠️ Mosquitto는 현재 localhost(127.0.0.1:1883)만 수신 → LAN 리스너(0.0.0.0:1883) 추가 필요 (sudo)
- [x] Phase 5: 노드 시각화 + 차시 이어하기 + 리플레이
  - flow_state(센서→ESP→MQTT→그래프→AI 펄스) + /api/flow/ws + 라이브데이터 연동(룰매칭시 ai노드까지)
  - node_explanations.json(학년별) + /api/flow/explain + /llm 깊은설명
  - checkpoint(자동저장: step_change 등, 측정요약 실시간 재계산) + /api/checkpoints/{latest,save,resume} + 이어하기 안전 재복창
  - replay(messages+readings 병합 타임라인) + /api/replay/{sessions,stream} SSE 배속
  - flow.html(자체 SVG+Alpine, 빔프로젝터 36px+, 데이터입자 애니메이션) + flow-fullscreen.html
  - 프론트: 이어하기 모달, ESP 위젯 sparkline. 자체 SVG 사용(React Flow/vis.js 미사용 — Pi 경량)
- [x] Phase 6: 데스크톱 통합 + 자동기동 + 학생 보호 (코드 완료, 적용은 콘솔)
  - systemd 4종(backend/warmup/watchdog/ap) + launcher.sh(키오스크) + watchdog.sh(5분 자가치유)
  - ScienceLab.desktop + assets/icon.png + student_lock.js(F11/F12/우클릭/새로고침 차단, 교사PIN 해제·30초 자동복귀)
  - admin/diagnose(Ollama·MQTT·디스크·메모리·온도·경고) 검증 OK
  - 배포: install/update/backup/restore/clone/uninstall.sh + first_boot.py + INSTALL.md
  - ⚠️ 적용은 콘솔(sudo/재부팅): bash scripts/install.sh → first_boot.py → reboot
- [ ] Phase 7: 재귀 학습 (세션 저장 → 벡터 인덱싱 → 교사 큐레이션 → 프롬프트 진화)

## Phase 2 반영 예정 실험 (사용자 제공)
| 학년 | 단원 | 실험 | 활용 센서/액추에이터 |
|---|---|---|---|
| 5 | 물체의 운동 | 자동 거리-속도 측정 | 초음파 + LLM이 v=d/t 자동 계산 |
| 5 | 물체의 운동 | RC카 가속도 실험 | 초음파 + 모터 + 충격센서 |
| 6 | 전기의 이용 | 자동문 시스템 | 초음파 + 모터 + 릴레이 |
| 융합 | SW교육 | 미니 자율주행 | 초음파 + 트래킹 + 모터 |
| 융합 | 환경 | 스마트 화분 자동 | 토양습도(추가 필요) + 모터(펌프) |

> 참고: 스마트 화분에는 토양습도 센서가 키트에 없을 수 있어 별도 구매 필요(예: 정전식 토양습도 센서).

## 설계 원칙
- 한국어 우선(UI/LLM/주석), 초등학생 대상(큰 폰트·직관적), 인터넷 없는 교실 가정
- 에러 메시지는 학생이 이해 가능한 한국어로
