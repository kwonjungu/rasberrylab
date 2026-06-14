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
from routers import chat as chat_router
from routers import checkpoint as checkpoint_router
from routers import data as data_router
from routers import flow as flow_router
from routers import replay as replay_router
from routers import sensors as sensors_router
from routers import session as session_router
from routers import stats as stats_router
from routers import teacher as teacher_router
from services import mqtt_client, ws_hub
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
    yield
    mqtt_client.stop()


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


# 프론트엔드(학생 화면) 정적 서빙 — 반드시 API 라우터 등록 이후 마지막에 마운트
_FRONTEND = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/", StaticFiles(directory=str(_FRONTEND), html=True), name="frontend")
