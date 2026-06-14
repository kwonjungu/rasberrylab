"""Science AI Lab — PDF 활동지 생성 (수업 종료 시)

A4 1장: 모둠·날짜·목표·가설·측정 그래프(matplotlib)·결론(LLM 1문단)·발문·교사메모.
한글은 번들된 NanumGothic TTF로 렌더(오프라인 보장).
교실 게시판 부착·가정 공유용.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

import httpx
import matplotlib

matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from .data_loader import store
from .db import get_conn

BASE = Path(__file__).resolve().parent.parent
FONT_PATH = BASE / "assets" / "fonts" / "NanumGothic-Regular.ttf"
REPORT_DIR = BASE.parent / "db" / "reports"
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
REPORT_MODEL = os.environ.get("SCIENCE_AI_REPORT_MODEL", "gemma3:1b")

# 폰트 등록 (reportlab + matplotlib)
pdfmetrics.registerFont(TTFont("Nanum", str(FONT_PATH)))
_FM = fm.FontProperties(fname=str(FONT_PATH))


def _readings(session_id: str) -> dict[str, list[tuple[int, float]]]:
    """센서별 (순번, 값) 시계열."""
    out: dict[str, list] = {}
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT sensor_key, value FROM sensor_readings WHERE session_id=? ORDER BY id",
            (session_id,),
        ).fetchall()
    for r in rows:
        out.setdefault(r["sensor_key"], []).append(r["value"])
    return out


def _chart(session_id: str, exp) -> Path | None:
    data = _readings(session_id)
    if not data:
        return None
    fig, ax = plt.subplots(figsize=(7, 3.2))
    for key, vals in data.items():
        ax.plot(range(1, len(vals) + 1), vals, marker="o", label=key)
    viz = (exp.data_visualization.model_dump() if exp and exp.data_visualization else {})
    ax.set_xlabel(viz.get("x_axis", "측정 순서"), fontproperties=_FM)
    ax.set_ylabel(viz.get("y_axis", "값"), fontproperties=_FM)
    ax.set_title("측정 데이터", fontproperties=_FM)
    if len(data) > 1:
        ax.legend(prop=_FM)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    img = REPORT_DIR / f"{session_id}_chart.png"
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(img, dpi=110)
    plt.close(fig)
    return img


def _llm_conclusion(exp, data: dict) -> str:
    """결론 1문단은 LLM 적극 사용. 실패 시 대체 문구."""
    if not exp:
        return "오늘 실험을 잘 마쳤어요. 측정한 값을 보며 무엇을 알게 됐는지 이야기해 봐요."
    summary = "; ".join(f"{k}: {len(v)}개 측정(최소 {min(v):.1f}, 최대 {max(v):.1f})" for k, v in data.items() if v)
    prompt = (
        f"초등학생 과학 실험 '{exp.title}' 결과를 한 문단(3문장 이내)으로 따뜻하게 요약해줘. "
        f"학습목표: {' '.join(exp.objectives)}. 측정요약: {summary or '데이터 없음'}. "
        "어려운 용어 없이, 무엇을 알게 됐는지 중심으로."
    )
    try:
        r = httpx.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": REPORT_MODEL, "prompt": prompt, "stream": False},
            timeout=120,
        )
        r.raise_for_status()
        return r.json().get("response", "").strip() or "오늘 실험을 잘 마쳤어요."
    except Exception:
        return "오늘 실험을 잘 마쳤어요. 측정한 값의 변화를 보며 무엇을 알게 됐는지 이야기해 봐요."


def generate(session_id: str) -> Path:
    with get_conn() as conn:
        s = conn.execute("SELECT * FROM sessions WHERE id=?", (session_id,)).fetchone()
    s = dict(s) if s else {"id": session_id}
    exp = store.experiment_by_id(s.get("experiment_id") or "")
    data = _readings(session_id)
    chart = _chart(session_id, exp)
    conclusion = _llm_conclusion(exp, data)

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    pdf_path = REPORT_DIR / f"{session_id}.pdf"
    c = canvas.Canvas(str(pdf_path), pagesize=A4)
    W, H = A4
    y = H - 25 * mm

    def line(txt, size=11, dy=7 * mm, bold_box=False):
        nonlocal y
        c.setFont("Nanum", size)
        c.drawString(20 * mm, y, txt)
        y -= dy

    # 머리말
    c.setFont("Nanum", 18)
    c.drawString(20 * mm, y, "🧪 과학 실험 활동지")
    y -= 12 * mm
    team = s.get("team_name") or "(모둠)"
    roles = ""
    try:
        ra = json.loads(s.get("role_assignments") or "{}")
        roles = ", ".join(f"{k}:{v}" for k, v in ra.items()) if ra else ""
    except Exception:
        pass
    line(f"모둠: {team}    날짜: {datetime.now().strftime('%Y-%m-%d')}    차시: {s.get('class_period') or '-'}", 11)
    if roles:
        line(f"역할: {roles}", 10)
    line(f"실험: {exp.title if exp else '-'}", 13)
    if exp and exp.objectives:
        line(f"학습목표: {' / '.join(exp.objectives)}", 10)
    if exp and exp.hypothesis_prompt:
        line(f"가설: {exp.hypothesis_prompt}", 10)

    # 그래프
    if chart:
        y -= 3 * mm
        c.drawImage(str(chart), 20 * mm, y - 70 * mm, width=170 * mm, height=70 * mm, preserveAspectRatio=True, mask="auto")
        y -= 76 * mm
    else:
        line("(측정 데이터가 없어요)", 10)

    # 결론(LLM)
    line("✏️ 결론", 13)
    c.setFont("Nanum", 11)
    for chunk in _wrap(conclusion, 42):
        c.drawString(22 * mm, y, chunk)
        y -= 6 * mm

    # 발문
    if exp and exp.post_questions:
        y -= 2 * mm
        line("💬 생각해 보기", 12)
        c.setFont("Nanum", 10)
        for q in exp.post_questions:
            for chunk in _wrap("• " + q, 46):
                c.drawString(22 * mm, y, chunk)
                y -= 5.5 * mm

    # 교사 메모 자리
    y -= 3 * mm
    line("👩‍🏫 선생님 메모:", 11)
    c.line(22 * mm, y, 190 * mm, y)

    c.setFont("Nanum", 8)
    c.drawString(20 * mm, 12 * mm, "Science AI Lab · 교실 게시판 부착용 · 학생 개인정보는 저장하지 않습니다")
    c.showPage()
    c.save()
    return pdf_path


def _wrap(text: str, width: int) -> list[str]:
    text = text.replace("\n", " ")
    return [text[i : i + width] for i in range(0, len(text), width)] or [""]
