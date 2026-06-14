"""Science AI Lab — MQTT 클라이언트 (paho-mqtt)

Mosquitto(localhost)를 구독해 ESP 데이터를 받아:
  1) sensor_registry 갱신 (info/heartbeat)
  2) data_buffer push + sensor_readings DB 기록
  3) sensor_rule_engine 실행 → 매칭 시 챗에 스크립트 메시지(rule) 자동 표시
  4) ws_hub로 실시간 푸시 (그래프·노드 시각화)

토픽:
  science-lab/sensors/{esp_id}/info
  science-lab/sensors/{esp_id}/heartbeat
  science-lab/sensors/{esp_id}/data/{sensor}
명령 발행:
  science-lab/commands/{esp_id}/{cmd}
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime

import paho.mqtt.client as mqtt

from . import data_buffer, flow_state, sensor_registry, sensor_rule_engine, ws_hub
from .data_loader import store
from .db import get_conn

BROKER = os.environ.get("MQTT_HOST", "127.0.0.1")
PORT = int(os.environ.get("MQTT_PORT", "1883"))
BASE = "science-lab"

_client: mqtt.Client | None = None


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _active_session() -> dict | None:
    try:
        with get_conn() as conn:
            r = conn.execute(
                "SELECT * FROM sessions WHERE status='active' ORDER BY started_at DESC LIMIT 1"
            ).fetchone()
            return dict(r) if r else None
    except Exception:
        return None


def _on_connect(client, userdata, flags, reason_code, properties=None):
    client.subscribe(f"{BASE}/sensors/#")
    print(f"📡 MQTT 연결됨 → {BASE}/sensors/# 구독")


def _on_message(client, userdata, msg):
    try:
        parts = msg.topic.split("/")
        # science-lab / sensors / {esp_id} / {kind} [/ {sensor}]
        if len(parts) < 4 or parts[1] != "sensors":
            return
        esp_id, kind = parts[2], parts[3]
        try:
            payload = json.loads(msg.payload.decode() or "{}")
        except Exception:
            payload = {}

        if kind == "info":
            sensor_registry.register(esp_id, payload)
            ws_hub.publish({"type": "esp_status", "esp_id": esp_id, "event": "info", "info": payload})
        elif kind == "heartbeat":
            sensor_registry.heartbeat(esp_id, payload)
            ws_hub.publish({"type": "esp_status", "esp_id": esp_id, "event": "heartbeat", "rssi": payload.get("rssi")})
        elif kind == "data" and len(parts) >= 5:
            sensor = parts[4]
            _handle_data(esp_id, sensor, payload)
    except Exception as exc:
        print("MQTT on_message 오류:", exc)


def _handle_data(esp_id: str, sensor: str, payload: dict):
    sensor_registry.touch(esp_id)
    value = payload.get("value")
    unit = payload.get("unit", "")
    try:
        fval = float(value)
    except (TypeError, ValueError):
        return

    data_buffer.push(esp_id, sensor, fval, unit)
    sess = _active_session()
    sid = sess.get("id") if sess else None
    step_n = (sess.get("current_step") if sess else 0) or 0

    # DB 기록
    try:
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO sensor_readings (session_id, sensor_key, value, step_n, created_at, esp_id, sensor_type, unit, ts) "
                "VALUES (?,?,?,?,?,?,?,?,?)",
                (sid, sensor, fval, step_n, _now(), esp_id, sensor, unit, _now()),
            )
    except Exception as exc:
        print("sensor_readings 기록 오류:", exc)

    # 실시간 그래프/노드 푸시
    ws_hub.publish({"type": "data", "esp_id": esp_id, "sensor": sensor, "value": fval, "unit": unit})

    # 룰 엔진 → 매칭 시 챗에 스크립트(rule) 자동 표시
    rule_hit = False
    if sess and sess.get("experiment_id"):
        step = store.step_dict(sess["experiment_id"], step_n)
        if step:
            hit = sensor_rule_engine.evaluate({sensor: fval}, step)
            if hit:
                rule_hit = True
                _log_and_push(sid, hit["scripted"], f"rule.{sensor}")

    # 노드 다이어그램 펄스 (룰/LLM 반응 있으면 AI 노드까지)
    flow_state.pulse_chain(esp_id, sensor, fval, unit, ai=rule_hit)


def _log_and_push(session_id, content, script_id):
    try:
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO messages (id, session_id, role, content, response_source, script_id, created_at) "
                "VALUES (?,?,?,?,?,?,?)",
                (uuid.uuid4().hex[:12], session_id, "assistant", content, "rule", script_id, _now()),
            )
    except Exception:
        pass
    ws_hub.publish({"type": "message", "source": "rule", "content": content, "script_id": script_id})


def publish_command(esp_id: str, cmd: str, payload: dict | None = None) -> bool:
    if not _client:
        return False
    _client.publish(f"{BASE}/commands/{esp_id}/{cmd}", json.dumps(payload or {}))
    return True


def start() -> None:
    global _client
    try:
        _client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2, client_id="science-ai-backend")
    except Exception:
        _client = mqtt.Client(client_id="science-ai-backend")  # 구버전 호환
    _client.on_connect = _on_connect
    _client.on_message = _on_message
    try:
        _client.connect(BROKER, PORT, keepalive=30)
        _client.loop_start()
        print(f"📡 MQTT 클라이언트 시작 ({BROKER}:{PORT})")
    except Exception as exc:
        print(f"⚠️ MQTT 연결 실패({BROKER}:{PORT}): {exc} — 브로커 기동 후 자동 재시도 안 함")


def stop() -> None:
    if _client:
        try:
            _client.loop_stop()
            _client.disconnect()
        except Exception:
            pass
