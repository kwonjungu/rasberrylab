"""Science AI Lab — USB 시리얼 리더 (ESP8266 직결)

WiFi/MQTT 없이 USB 케이블만으로 동작하는 경로. ESP가 시리얼에 JSON 한 줄씩
출력하면(아래 형식) 이를 읽어 MQTT와 *동일한* 파이프라인에 흘려보낸다:
  data_buffer push + DB 기록 + ws_hub 실시간 푸시 + 룰 엔진 + 노드 펄스.

ESP → 시리얼 출력(개행 구분 JSON):
  {"type":"info","sensor":"temperature","board_type":"nodemcu-usb"}
  {"type":"data","sensor":"temperature","value":22.4,"unit":"celsius","quality":"good"}
  {"type":"heartbeat","uptime_s":12}
type 가 없으면 value 유무로 data/info 를 추정한다(펌웨어 호환).

환경변수:
  SERIAL_PORT  (기본 /dev/ttyUSB0)
  SERIAL_BAUD  (기본 115200)
  SERIAL_ESP_ID(기본 usb-01)  — 시리얼은 1:1 이라 보드 1개당 1 ID
  SERIAL_ENABLE(기본 auto)    — auto: 포트 있으면 시작 / off: 비활성
"""

from __future__ import annotations

import json
import os
import threading
import time

from . import sensor_registry, ws_hub
from .mqtt_client import _handle_data  # MQTT와 동일한 수집 파이프라인 재사용

PORT = os.environ.get("SERIAL_PORT", "/dev/ttyUSB0")
BAUD = int(os.environ.get("SERIAL_BAUD", "115200"))
ESP_ID = os.environ.get("SERIAL_ESP_ID", "usb-01")
ENABLE = os.environ.get("SERIAL_ENABLE", "auto").lower()

_thread: threading.Thread | None = None
_stop = threading.Event()


def _handle_line(line: str) -> None:
    line = line.strip()
    if not line or line[0] != "{":
        return  # 부팅 로그 등 비-JSON 줄은 무시
    try:
        msg = json.loads(line)
    except Exception:
        return
    kind = msg.get("type") or ("data" if "value" in msg else "info")
    if kind == "info":
        sensor_registry.register(ESP_ID, {"board_type": msg.get("board_type", "nodemcu-usb"),
                                           "sensor": msg.get("sensor")})
        ws_hub.publish({"type": "esp_status", "esp_id": ESP_ID, "event": "info", "info": msg})
    elif kind == "heartbeat":
        sensor_registry.heartbeat(ESP_ID, msg)
        ws_hub.publish({"type": "esp_status", "esp_id": ESP_ID, "event": "heartbeat"})
    elif kind == "data":
        sensor = msg.get("sensor") or "value"
        _handle_data(ESP_ID, sensor, msg)


def _run() -> None:
    import serial  # pyserial

    while not _stop.is_set():
        try:
            ser = serial.Serial(PORT, BAUD, timeout=1)
        except Exception as exc:
            print(f"🔌 시리얼 열기 실패({PORT}@{BAUD}): {exc} — 3초 후 재시도")
            if _stop.wait(3):
                return
            continue
        # 보드가 연결돼 있다는 사실만으로 활성 등록(데이터 전이라도 표시)
        sensor_registry.register(ESP_ID, {"board_type": "nodemcu-usb"})
        print(f"🔌 USB 시리얼 연결됨 → {PORT}@{BAUD} (esp_id={ESP_ID})")
        try:
            while not _stop.is_set():
                raw = ser.readline()
                if not raw:
                    continue
                try:
                    _handle_line(raw.decode("utf-8", "ignore"))
                except Exception as exc:
                    print("시리얼 처리 오류:", exc)
        except Exception as exc:
            print(f"🔌 시리얼 끊김({PORT}): {exc} — 재연결")
        finally:
            try:
                ser.close()
            except Exception:
                pass
        if _stop.wait(2):
            return


def start() -> None:
    global _thread
    if ENABLE == "off":
        print("🔌 USB 시리얼 비활성(SERIAL_ENABLE=off)")
        return
    if ENABLE == "auto" and not os.path.exists(PORT):
        print(f"🔌 USB 시리얼 포트 없음({PORT}) — 시리얼 리더 미시작")
        return
    _stop.clear()
    _thread = threading.Thread(target=_run, name="serial-reader", daemon=True)
    _thread.start()
    print(f"🔌 USB 시리얼 리더 시작({PORT}@{BAUD})")


def stop() -> None:
    _stop.set()
