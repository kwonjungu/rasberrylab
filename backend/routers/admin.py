"""Science AI Lab — 관리/진단 API (Phase 6, 교사 모드)

/api/admin/diagnose : 백엔드·Ollama·Mosquitto·디스크·메모리·온도·세션 한눈 점검.
인터넷 없는 교실에서 교사가 문제를 빨리 파악하도록 한국어 경고 동반.
"""

from __future__ import annotations

import os
import shutil
import subprocess

import httpx
from fastapi import APIRouter

from services import sensor_registry
from services.db import get_conn

router = APIRouter(prefix="/api/admin", tags=["admin"])

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")


def _cpu_temp() -> str:
    try:
        with open("/sys/class/thermal/thermal_zone0/temp") as f:
            return f"{int(f.read()) / 1000:.0f}℃"
    except Exception:
        return "?"


def _mem() -> str:
    try:
        info = {}
        with open("/proc/meminfo") as f:
            for line in f:
                k, v = line.split(":")
                info[k] = int(v.strip().split()[0])  # kB
        free_gb = info.get("MemAvailable", 0) / 1024 / 1024
        total_gb = info.get("MemTotal", 0) / 1024 / 1024
        return f"free {free_gb:.1f}GB / {total_gb:.1f}GB"
    except Exception:
        return "?"


def _disk(path: str) -> str:
    try:
        u = shutil.disk_usage(path)
        return f"{u.used * 100 // u.total}%"
    except Exception:
        return "?"


def _service_active(name: str) -> bool:
    try:
        r = subprocess.run(["systemctl", "is-active", name], capture_output=True, text=True, timeout=3)
        return r.stdout.strip() == "active"
    except Exception:
        return False


@router.get("/diagnose")
async def diagnose():
    warnings: list[str] = []

    # Ollama
    ollama = "down"
    try:
        r = httpx.get(f"{OLLAMA_URL}/api/tags", timeout=4)
        models = [m["name"] for m in r.json().get("models", [])]
        ollama = f"ok ({', '.join(models[:3])})" if models else "ok (모델 없음)"
        if not models:
            warnings.append("Ollama에 모델이 없어요. `ollama pull gemma3:1b` 필요.")
    except Exception:
        warnings.append("Ollama에 연결되지 않아요. ollama 서비스를 확인하세요.")

    mosq = _service_active("mosquitto")
    if not mosq:
        warnings.append("Mosquitto(MQTT)가 꺼져 있어요. 센서가 연결되지 않습니다.")

    temp = _cpu_temp()
    try:
        if temp != "?" and int(temp.rstrip("℃")) >= 70:
            warnings.append(f"CPU 온도가 높아요({temp}). 통풍·방열판을 확인하세요.")
    except Exception:
        pass

    sd = _disk("/")
    ssd = _disk("/mnt/nvme")
    try:
        if int(ssd.rstrip("%")) >= 90:
            warnings.append("SSD 공간이 거의 찼어요. 오래된 백업·리포트를 정리하세요.")
    except Exception:
        pass

    with get_conn() as conn:
        last = conn.execute("SELECT started_at FROM sessions ORDER BY started_at DESC LIMIT 1").fetchone()

    return {
        "backend": "ok",
        "ollama": ollama,
        "mosquitto": "ok" if mosq else "down",
        "esp_devices": sensor_registry.active(),
        "disk_usage": {"sd": sd, "ssd": ssd},
        "memory": _mem(),
        "temperature": temp,
        "last_session": last["started_at"] if last else None,
        "warnings": warnings,
    }
