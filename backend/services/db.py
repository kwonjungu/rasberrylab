"""Science AI Lab — SQLite 연결/초기화 (lab.db, SSD).

세션 상태·메시지·실험기록·뱃지를 저장한다. 개인정보(별명)는
세션 종료 시 NULL로 지운다(role_manager/ session end 에서 처리).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DB_DIR = PROJECT_ROOT / "db"
DB_PATH = DB_DIR / "lab.db"
SCHEMA_PATH = DB_DIR / "schema.sql"


def get_conn() -> sqlite3.Connection:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")  # 잦은 저장에 유리, SD가 아닌 SSD
    return conn


def init_db() -> None:
    """스키마 적용(존재하면 무시) + 컬럼 마이그레이션. 부팅 시 1회 호출."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    sql = SCHEMA_PATH.read_text(encoding="utf-8")
    with get_conn() as conn:
        conn.executescript(sql)
        _migrate(conn)


def _migrate(conn) -> None:
    """기존 테이블에 누락된 컬럼을 추가(ADD COLUMN은 멱등 처리)."""
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(sensor_readings)")}
    # Phase 4: ESP 기반 컬럼 추가 (Phase 3의 session_id/sensor_key와 공존)
    for name, decl in [
        ("esp_id", "TEXT"),
        ("sensor_type", "TEXT"),
        ("unit", "TEXT"),
        ("quality", "TEXT"),
        ("ts", "TEXT"),
    ]:
        if name not in cols:
            conn.execute(f"ALTER TABLE sensor_readings ADD COLUMN {name} {decl}")
