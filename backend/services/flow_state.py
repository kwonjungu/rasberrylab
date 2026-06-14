"""Science AI Lab — 노드 흐름 상태 (Phase 5)

토폴로지: [센서]→[ESP]→[MQTT]→[그래프]→[AI]
데이터가 들어오면 각 노드를 순서대로 pulse 시키고 ws_hub(/ws/flow)로 푸시한다.
프론트는 상태만 받아 SVG 애니메이션을 트리거한다.
"""

from __future__ import annotations

from . import ws_hub

NODES = ["sensor", "esp", "mqtt", "graph", "ai"]

# 노드별 pulse 지속(ms) — 프론트 애니메이션 동기화용 힌트
PULSE_MS = {"sensor": 1000, "esp": 500, "mqtt": 300, "graph": 500, "ai": 800}


def pulse_chain(esp_id: str, sensor: str, value, unit: str = "", ai: bool = False) -> None:
    """데이터 1건 도착 → 센서~그래프 펄스. ai=True면 AI 노드도 펄스(룰/LLM 반응)."""
    seq = ["sensor", "esp", "mqtt", "graph"]
    if ai:
        seq.append("ai")
    ws_hub.publish({
        "type": "flow",
        "esp_id": esp_id,
        "sensor": sensor,
        "value": value,
        "unit": unit,
        "sequence": seq,
        "pulse_ms": {n: PULSE_MS[n] for n in seq},
    })


def node_error(node: str, esp_id: str | None = None) -> None:
    ws_hub.publish({"type": "flow_error", "node": node, "esp_id": esp_id})
