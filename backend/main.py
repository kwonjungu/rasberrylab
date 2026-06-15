"""Science AI Lab — FastAPI 백엔드 (Phase 1 스켈레톤)

초등학생용 로컬 LLM 과학 실험 플랫폼.
모든 처리는 교실 내부(Ollama, 추후 MQTT)에서 이루어지며 인터넷이 필요 없다.
"""

import os
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from routers import admin as admin_router
from routers import analytics as analytics_router
from routers import chat as chat_router
from routers import checkpoint as checkpoint_router
from routers import curation as curation_router
from routers import data as data_router
from routers import flow as flow_router
from routers import replay as replay_router
from routers import sensors as sensors_router
from routers import session as session_router
from routers import stats as stats_router
from routers import teacher as teacher_router
from services import mqtt_client, serial_reader, ws_hub
from services.data_loader import store
from services.db import init_db

# --- 설정 (환경변수로 덮어쓰기 가능) ---
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
# 빠른 응답이 중요한 채팅 기본 모델. 품질 우선 시 gemma3:4b 로 교체.
DEFAULT_MODEL = os.environ.get("SCIENCE_AI_MODEL", "gemma3:1b")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 부팅 시 DB 초기화 + 4개 JSON 로드 + 무결성 검증
    init_db()
    store.load()
    if store.errors:
        print("⚠️ 데이터 오류 발견:")
        for e in store.errors:
            print("  ", e)
    print(f"✅ 데이터 로드: 센서 {len(store.sensors)} · 실험 {len(store.experiments)} · 단원 {len(store.unit_index())} · 스크립트 {'OK' if store.dialogue else '없음'}")
    # WS 허브에 현재 asyncio 루프 등록 + MQTT 클라이언트 시작
    import asyncio
    ws_hub.set_loop(asyncio.get_running_loop())
    mqtt_client.start()
    serial_reader.start()   # USB 직결 ESP(시리얼) — 포트 있으면 자동 시작
    yield
    mqtt_client.stop()
    serial_reader.stop()


app = FastAPI(title="Science AI Lab", version="0.3.0", lifespan=lifespan)
app.include_router(data_router.router)
app.include_router(session_router.router)
app.include_router(chat_router.router)
app.include_router(stats_router.router)
app.include_router(teacher_router.router)
app.include_router(sensors_router.router)
app.include_router(flow_router.router)
app.include_router(checkpoint_router.router)
app.include_router(replay_router.router)
app.include_router(admin_router.router)
app.include_router(curation_router.router)
app.include_router(analytics_router.router)

# 프론트(로컬 정적 파일)에서의 호출 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    """서비스 + Ollama 연결 상태 점검."""
    ollama_ok = False
    models: list[str] = []
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{OLLAMA_URL}/api/tags")
            resp.raise_for_status()
            models = [m["name"] for m in resp.json().get("models", [])]
            ollama_ok = True
    except Exception:
        # 학생 화면에는 노출되지 않는 내부 점검용이므로 조용히 실패 처리
        pass

    return {
        "status": "ok",
        "service": "science-ai",
        "default_model": DEFAULT_MODEL,
        "ollama": {"connected": ollama_ok, "url": OLLAMA_URL, "models": models},
    }


@app.get("/api/ollama/test")
async def ollama_test(prompt: str = "안녕"):
    """기본 모델로 한 번 응답을 받아 LLM 연결을 확인한다."""
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={"model": DEFAULT_MODEL, "prompt": prompt, "stream": False},
            )
            resp.raise_for_status()
            data = resp.json()
        return {
            "model": DEFAULT_MODEL,
            "prompt": prompt,
            "response": data.get("response", "").strip(),
            "eval_tokens": data.get("eval_count"),
        }
    except Exception as exc:  # 학생도 이해할 수 있는 한국어 메시지
        return JSONResponse(
            status_code=503,
            content={
                "error": "AI 선생님에 연결하지 못했어요. 잠시 후 다시 시도해 주세요. 🙇",
                "detail": str(exc),
            },
        )


@app.post("/api/helpbot")
async def helpbot(payload: dict):
    """우하단 안내 챗봇 하네스 — 과학/앱사용법 한정.
    프런트의 하드코딩 FAQ가 못 맞춘 질문만 여기로 온다. Ollama가 있으면 스코프
    시스템 프롬프트로 짧게 답하고, 없으면 503 으로 우아하게 실패(프런트가 안내 처리)."""
    text = (payload.get("text") or "").strip()
    system = payload.get("system") or (
        "너는 초등 과학 실험 앱의 안내 도우미 '라비'다. 이 앱의 사용법과 초등 과학 개념에 "
        "대해서만 한국어로 2~3문장으로 쉽고 다정하게 답하고, 그 외 주제는 정중히 거절한다."
    )
    if not text:
        return JSONResponse(status_code=400, content={"error": "질문이 비어 있어요."})
    prompt = f"{system}\n\n학생 질문: {text}\n라비의 답변:"
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={"model": DEFAULT_MODEL, "prompt": prompt, "stream": False,
                      "options": {"temperature": 0.3, "num_predict": 160}},
            )
            resp.raise_for_status()
            data = resp.json()
        return {"reply": data.get("response", "").strip(), "source": "ollama"}
    except Exception as exc:
        # Ollama 미연결 — 프런트가 FAQ 안내로 대체한다.
        return JSONResponse(status_code=503, content={"error": "ollama_unavailable", "detail": str(exc)})


# 프론트엔드(학생 화면) 정적 서빙 — 반드시 API 라우터 등록 이후 마지막에 마운트
_FRONTEND = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/", StaticFiles(directory=str(_FRONTEND), html=True), name="frontend")
