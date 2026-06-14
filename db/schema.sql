-- Science AI Lab — SQLite 스키마 (lab.db, SSD에 저장)
-- 1 Pi = 1 모둠. 개인정보 영구저장 안 함(별명은 세션 종료 시 NULL).

CREATE TABLE IF NOT EXISTS sessions (
  id                 TEXT PRIMARY KEY,
  team_name          TEXT,
  role_assignments   TEXT,          -- JSON: {"experiment":"지민",...} (종료 시 NULL)
  grade              INTEGER,
  unit_id            TEXT,
  experiment_id      TEXT,
  class_period       TEXT,
  started_at         TEXT,
  ended_at           TEXT,
  current_step       INTEGER DEFAULT 0,
  current_mode       TEXT DEFAULT 'greeting',
  status             TEXT DEFAULT 'active',   -- active|paused|ended
  safety_ritual_done INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS messages (
  id              TEXT PRIMARY KEY,
  session_id      TEXT,
  role            TEXT,    -- user|assistant|system|teacher_injected
  content         TEXT,
  quick_replies   TEXT,    -- JSON 배열
  spoken_by       TEXT,    -- 어느 역할이 말했는지
  response_source TEXT,    -- scripted|llm|rule
  script_id       TEXT,
  model           TEXT,
  latency_ms      INTEGER,
  created_at      TEXT
);

CREATE TABLE IF NOT EXISTS experiment_runs (
  id            TEXT PRIMARY KEY,
  session_id    TEXT,
  experiment_id TEXT,
  started_at    TEXT,
  completed_at  TEXT,
  outcome       TEXT,
  help_calls    INTEGER DEFAULT 0,
  teacher_notes TEXT
);

CREATE TABLE IF NOT EXISTS badges (
  id         TEXT PRIMARY KEY,
  session_id TEXT,
  badge_type TEXT,
  awarded_at TEXT
);

-- 센서 측정값 시계열 (PDF 그래프·이상값 판단용)
-- Phase 4에서 esp_id/sensor_type/unit/quality/ts 컬럼이 migrate로 추가됨(db.py)
CREATE TABLE IF NOT EXISTS sensor_readings (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id TEXT,
  sensor_key TEXT,
  value      REAL,
  step_n     INTEGER,
  created_at TEXT
);

-- Phase 4: 활성 ESP8266 보드 목록
CREATE TABLE IF NOT EXISTS esp_devices (
  id          TEXT PRIMARY KEY,    -- 'esp-01'
  board_type  TEXT,
  sensor_type TEXT,
  first_seen  TEXT,
  last_seen   TEXT,
  rssi        INTEGER,
  status      TEXT                 -- alive|dead
);

-- Phase 4: 센서 이벤트(임계값 통과/이상/끊김)
CREATE TABLE IF NOT EXISTS sensor_events (
  id                    INTEGER PRIMARY KEY AUTOINCREMENT,
  esp_id                TEXT,
  event_type            TEXT,      -- threshold_crossed|anomaly|disconnect
  payload               TEXT,
  triggered_response_id TEXT,
  ts                    TEXT
);

-- Phase 5: 차시 이어하기 체크포인트
CREATE TABLE IF NOT EXISTS checkpoints (
  id                  TEXT PRIMARY KEY,
  session_id          TEXT,
  step_n              INTEGER,
  mode                TEXT,
  active_esp_ids      TEXT,
  recent_messages     TEXT,
  measurement_summary TEXT,
  teacher_notes       TEXT,
  saved_at            TEXT,
  reason              TEXT      -- auto_5min|step_change|manual|shutdown
);

-- Phase 5: 노드 흐름 이벤트(분석/리플레이 보조)
CREATE TABLE IF NOT EXISTS flow_events (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id TEXT,
  node       TEXT,
  state      TEXT,
  ts         TEXT
);

-- Phase 7: 벡터 임베딩(BLOB) + 메타 (numpy 코사인 검색)
CREATE TABLE IF NOT EXISTS vector_embeddings (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  source_type TEXT,      -- qa|question
  source_id   TEXT,      -- message id 등
  grade       INTEGER,
  unit_id     TEXT,
  experiment_id TEXT,
  content     TEXT,      -- 임베딩 대상 텍스트(익명화됨)
  answer      TEXT,      -- 함께 보관할 답변(있으면)
  embedding   BLOB,      -- float32 768차원
  curated_status TEXT DEFAULT 'pending',  -- pending|approved|rejected
  created_at  TEXT
);

-- Phase 7: 교사 검수 큐
CREATE TABLE IF NOT EXISTS curation_queue (
  id          TEXT PRIMARY KEY,
  message_id  TEXT,
  session_id  TEXT,
  question    TEXT,
  answer      TEXT,
  grade       INTEGER,
  reason      TEXT,      -- 자동 분류 사유
  status      TEXT DEFAULT 'pending',  -- pending|approved|rejected|edited
  edited_answer TEXT,
  created_at  TEXT
);

-- Phase 7: 시스템 프롬프트 버전(롤백 가능)
CREATE TABLE IF NOT EXISTS prompt_versions (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  version    INTEGER,
  addon      TEXT,       -- prompt_builder에 병합되는 학습 내용
  active      INTEGER DEFAULT 0,
  approved_n  INTEGER,
  rejected_n  INTEGER,
  created_at  TEXT
);

-- Phase 7: 환각/오답 탐지 로그
CREATE TABLE IF NOT EXISTS anomaly_log (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  message_id TEXT,
  reason     TEXT,
  detail     TEXT,
  ts         TEXT
);

CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);
CREATE INDEX IF NOT EXISTS idx_checkpoints_session ON checkpoints(session_id);
CREATE INDEX IF NOT EXISTS idx_curation_status ON curation_queue(status);
CREATE INDEX IF NOT EXISTS idx_messages_source  ON messages(response_source);
CREATE INDEX IF NOT EXISTS idx_readings_session ON sensor_readings(session_id);
