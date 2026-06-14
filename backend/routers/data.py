"""Science AI Lab — 데이터 조회 + 무결성 검증 라우터.

sensors / experiments / curriculum / onboarding 의 단일 진실 소스를
프론트엔드·LLM 프롬프트에 제공하고, 데이터 무결성을 점검한다.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from services.data_loader import store

router = APIRouter(prefix="/api/data", tags=["data"])


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
    return {"count": len(items), "experiments": [e.model_dump() for e in items]}


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
