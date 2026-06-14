"""Science AI Lab — 센서 룰 엔진

experiments.json step 의 sensor_thresholds 를 평가해 정해진 스크립트 멘트를
반환한다. LLM보다 먼저 동작(결정적). 매칭이 없으면 None → 라우터가
정상범위 격려(throttle) 또는 LLM 해석으로 넘긴다.

지원 range 문법:
  "> 5", ">= 20", "< 0", "<= 3", "== 1"
  "0 ~ 5"            (이상~이하 구간)
  "dry" / "wet"      (의미 토큰: 값이 큰지/작은지로 해석, 모듈 따라 반전 가능)
"""

from __future__ import annotations

import re
from typing import Any, Optional

_NUM = r"-?\d+(?:\.\d+)?"


def _match_range(value: float, expr: str) -> bool:
    expr = expr.strip()

    m = re.fullmatch(rf"({_NUM})\s*~\s*({_NUM})", expr)
    if m:
        lo, hi = float(m.group(1)), float(m.group(2))
        return lo <= value <= hi

    m = re.fullmatch(rf"(>=|<=|>|<|==)\s*({_NUM})", expr)
    if m:
        op, num = m.group(1), float(m.group(2))
        return {
            ">": value > num,
            "<": value < num,
            ">=": value >= num,
            "<=": value <= num,
            "==": value == num,
        }[op]

    return False


def evaluate(sensor_values: dict[str, Any], step: dict) -> Optional[dict]:
    """센서값이 step의 임계값을 통과하면 {scripted, sensor, range} 반환, 아니면 None.

    sensor_values 예: {"temperature": 3.2} 또는 {"soil_moisture": "dry"}
    """
    thresholds = (step or {}).get("sensor_thresholds") or {}
    for sensor_key, rules in thresholds.items():
        if sensor_key not in sensor_values:
            continue
        raw = sensor_values[sensor_key]
        for rule in rules:
            rng = str(rule.get("range", "")).strip()
            scripted = rule.get("scripted", "")
            # 의미 토큰(dry/wet 등) — 문자열 직접 일치
            if isinstance(raw, str):
                if raw.strip().lower() == rng.lower():
                    return {"scripted": scripted, "sensor": sensor_key, "range": rng}
                continue
            # 숫자 비교
            try:
                value = float(raw)
            except (TypeError, ValueError):
                continue
            if _match_range(value, rng):
                return {"scripted": scripted, "sensor": sensor_key, "range": rng}
    return None


# ----- 내장 테스트 -----
if __name__ == "__main__":
    step = {
        "sensor_thresholds": {
            "temperature": [
                {"range": "> 5", "scripted": "아직 차가워지는 중 🥶"},
                {"range": "0 ~ 5", "scripted": "이제 곧 얼겠다! 👀"},
                {"range": "< 0", "scripted": "와! 얼음이 되고 있어 ❄"},
            ],
            "soil_moisture": [
                {"range": "dry", "scripted": "🌵 흙이 말랐어요! 펌프 작동 💧"},
                {"range": "wet", "scripted": "🌱 흙이 촉촉해요."},
            ],
        }
    }
    for sv in [{"temperature": 8}, {"temperature": 3}, {"temperature": -2}, {"soil_moisture": "dry"}]:
        print(sv, "→", evaluate(sv, step))
