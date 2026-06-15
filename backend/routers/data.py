"""Science AI Lab — 데이터 조회 + 무결성 검증 라우터.

sensors / experiments / curriculum / onboarding 의 단일 진실 소스를
프론트엔드·LLM 프롬프트에 제공하고, 데이터 무결성을 점검한다.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from services.data_loader import store

router = APIRouter(prefix="/api/data", tags=["data"])


def _port_for(sensor) -> str:
    """멀티포트 펌웨어(firmware_multi.ino) 규칙에 맞춘 권장 포트.
    아날로그→A0(유일), 온습도/방수온도→D2, 그 외 디지털→D5."""
    sid = sensor.id
    if sid in ("dht11", "digital-temp", "ds18b20"):
        return "D2"
    if (getattr(sensor, "interface", "") or "").lower() == "analog":
        return "A0"
    return "D5"


def _wiring_hints(exp) -> list[str]:
    """라비가 시작할 때 들려주는 '어디에 뭘 꽂아라' 안내(쉬운 한국어)."""
    by_id = {s.id: s for s in store.sensors}
    hints: list[str] = []
    for sid in (exp.required_sensors + exp.required_actuators):
        s = by_id.get(sid)
        if not s:
            continue
        port = _port_for(s)
        name = s.name_ko or sid
        where = "아날로그 자리 <b>A0</b>" if port == "A0" else f"<b>{port}</b> 자리"
        hints.append(
            f"🔌 <b>{name}</b>를 꺼내자! 신호선(S 또는 화살표)은 보드의 {where}에, "
            f"가운데 선(VCC)은 <b>3V3</b>, 검은 선(GND)은 <b>GND</b>에 꼭 꽂아줘."
        )
    return hints


@router.get("/validate")
async def validate():
    """4개 JSON의 무결성 리포트(항목 수, 학년별 실험 수, 미사용 센서, 누락 매핑, 오류/경고)."""
    return store.report()


@router.get("/sensors")
async def get_sensors(category: str | None = Query(None), type: str | None = Query(None)):
    items = store.sensors
    if category:
        items = [s for s in items if s.category == category]
    if type:
        items = [s for s in items if s.type == type]
    return {"count": len(items), "sensors": [s.model_dump() for s in items]}


@router.get("/sensors/{sensor_id}")
async def get_sensor(sensor_id: str):
    for s in store.sensors:
        if s.id == sensor_id:
            return s.model_dump()
    return JSONResponse(status_code=404, content={"error": f"'{sensor_id}' 센서를 찾을 수 없어요."})


@router.get("/experiments")
async def get_experiments(grade: int | None = Query(None), unit_id: str | None = Query(None)):
    items = store.experiments
    if grade is not None:
        items = [e for e in items if e.grade == grade]
    if unit_id:
        items = [e for e in items if e.unit_id == unit_id]
    out = []
    for e in items:
        d = e.model_dump()
        d["wiring_hints"] = _wiring_hints(e)
        out.append(d)
    return {"count": len(items), "experiments": out}


@router.get("/experiments/{exp_id}")
async def get_experiment(exp_id: str):
    for e in store.experiments:
        if e.id == exp_id:
            return e.model_dump()
    return JSONResponse(status_code=404, content={"error": f"'{exp_id}' 실험을 찾을 수 없어요."})


@router.get("/units")
async def get_units(grade: int | None = Query(None)):
    if not store.curriculum:
        return {"count": 0, "units": []}
    units = []
    for gb in store.curriculum.grades:
        if grade is not None and gb.grade != grade:
            continue
        for u in gb.units:
            units.append({"grade": gb.grade, "semester": gb.semester, **u.model_dump()})
    return {"count": len(units), "units": units}


@router.get("/onboarding")
async def get_onboarding():
    if not store.onboarding:
        return JSONResponse(status_code=404, content={"error": "온보딩 데이터가 없어요."})
    return store.onboarding.model_dump()
