# -*- coding: utf-8 -*-
"""Nano Banana(gemini-2.5-flash-image) 로 실제 일러스트를 생성해 에셋에 추가.
 - httpx 가 이 환경에서 SSL 실패 → curl 서브프로세스로 호출
 - 생성 PNG 를 '기존 .svg 파일명'에 <image> 로 임베드(앱 참조 변경 0)
 - 429/일시오류 백오프, 이미 처리한 파일 건너뛰기(재개 가능)
환경변수 GEMINI_API_KEY 필요.
"""
from __future__ import annotations
import base64, json, os, subprocess, sys, time, tempfile
from pathlib import Path

KEY = os.environ["GEMINI_API_KEY"]
MODEL = "gemini-2.5-flash-image"
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={KEY}"
ROOT = Path(__file__).resolve().parent.parent.parent
ASSETS = ROOT / "frontend" / "assets"

STYLE = (" flat vector cartoon illustration, thick clean rounded outlines, soft pastel colors, "
         "plain white background, kid-friendly, cheerful, centered, no text, no watermark")
LABI = ("Labi, a cute friendly sky-blue lab-assistant robot with a glowing cyan antenna, "
        "big cyan eyes and pink cheeks")

# 마스코트
MASCOT = {
  "mascot/labi.svg": f"{LABI}, waving one hand with a warm smile, holding a small magnifying glass.{STYLE}",
  "mascot/labi-cheer.svg": f"{LABI}, both arms raised celebrating, holding a gold medal, confetti and sparkles around.{STYLE}",
}
# 학년 구역(텍스트 없는 풍경 배지)
REGION = {
  "region/g3.svg": f"a sunny green meadow science village with tiny cottages and curiosity sparkles, inside a rounded shield badge with green ribbon.{STYLE}",
  "region/g4.svg": f"rolling blue-indigo hills with a telescope and a winding discovery path, inside a rounded shield badge with indigo ribbon.{STYLE}",
  "region/g5.svg": f"an amber experiment valley with bubbling beakers and gentle electric sparks, inside a rounded shield badge with amber ribbon.{STYLE}",
  "region/g6.svg": f"a pink mountain peak with a small rocket and flags at the summit, inside a rounded shield badge with magenta ribbon.{STYLE}",
  "region/fx.svg": f"a cute futuristic cyan space station with small robots and circuits, inside a rounded shield badge with cyan ribbon.{STYLE}",
}
# 단계 삽화(라비가 돕는 장면)
STEPS = {
  "linear-hall-plug":   "kid hands plugging a small hall sensor into a breadboard, Labi pointing helpfully",
  "magnet-1cm":         "a red horseshoe magnet held about 1cm from a sensor, glowing magnetic field, a small ruler",
  "magnet-far":         "a red horseshoe magnet moved far from a sensor, faint fading field arcs, a double-headed distance arrow",
  "sound-quiet":        "a quiet classroom, a finger on lips gesture, a small sound meter showing a low level",
  "sound-clap":         "two hands clapping loudly with big sound waves, a sound meter spiking high",
  "ice-sensor":         "placing a thermometer probe into a cup of ice cubes",
  "ice-melt":           "ice cubes slowly melting into water with droplets, a thermometer beside",
  "light-bright":       "a bright lamp shining onto a light sensor, sunny and cheerful",
  "light-block":        "a hand blocking light and casting a soft shadow onto a light sensor",
  "shock-buzzer":       "wiring a shock sensor to a small buzzer on a breadboard",
  "shake-table":        "hands gently shaking a desk with a small model, wobble motion lines, a tiny volcano",
  "warm-water":         "pouring warm water into a cup with rising steam",
  "insulation":         "two cups, one wrapped with wool and foil for insulation, comparing warmth",
  "ultrasonic-setup":   "mounting an HC-SR04 ultrasonic distance sensor facing a small toy car",
  "car-roll":           "a cute toy car rolling down a gentle ramp",
  "calc-speed":         "a kid holding a stopwatch and a ruler, computing speed, distance divided by time",
  "auto-light-wire":    "wiring an LED and a light sensor circuit on a breadboard",
  "cover-sensor":       "covering a sensor with a hand or small box to test it",
  "heartbeat-rest":     "a child sitting calmly with a pulse sensor clipped on a fingertip, a small heart",
  "heartbeat-exercise": "a child jumping and running then checking pulse, a beating red heart",
  "rgb-red":            "an RGB LED glowing bright red on a breadboard",
  "rgb-mix":            "an RGB LED mixing red green blue light into a rainbow",
  "rc-build":           "assembling a small RC car with simple tools",
  "rc-run":             "an RC race car speeding on a track with motion lines",
  "rc-crash":           "an RC car gently bumping a soft cushion wall, cartoon impact stars",
  "door-build":         "building a small model automatic sliding door with a servo motor",
  "door-open":          "a friendly person approaching and an automatic door sliding open",
  "self-driving-build": "assembling a small robot car with line and obstacle sensors",
  "follow-line":        "a robot car following a thick black line on a white floor",
  "avoid-obstacle":     "a robot car turning to avoid an orange traffic cone",
  "soil-sensor":        "inserting a moisture sensor into the soil of a small flower pot",
  "auto-water":         "a tiny pump automatically watering a green sprout in a pot",
}

def targets():
    for path, prompt in MASCOT.items():
        yield ASSETS / path, prompt
    for path, prompt in REGION.items():
        yield ASSETS / path, prompt
    for key, scene in STEPS.items():
        yield ASSETS / "steps" / f"{key}.svg", f"{scene}. {LABI} helping nearby.{STYLE}"

def png_size(b: bytes):
    # PNG IHDR: width/height at bytes 16..24
    return int.from_bytes(b[16:20], "big"), int.from_bytes(b[20:24], "big")

def wrap_svg(png: bytes) -> str:
    w, h = png_size(png)
    b64 = base64.b64encode(png).decode()
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">'
            f'<image width="{w}" height="{h}" href="data:image/png;base64,{b64}"/></svg>')

def generate(prompt: str) -> bytes | None:
    body = {"contents": [{"parts": [{"text": prompt}]}]}
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(body, f); bodyfile = f.name
    try:
        for attempt in range(4):
            p = subprocess.run(
                ["curl", "-s", "--max-time", "150", "-X", "POST", URL,
                 "-H", "Content-Type: application/json", "-d", f"@{bodyfile}"],
                capture_output=True, text=True)
            out = p.stdout
            try:
                d = json.loads(out)
            except Exception:
                time.sleep(3 + attempt * 4); continue
            if "candidates" in d:
                for part in d["candidates"][0]["content"]["parts"]:
                    inl = part.get("inlineData") or part.get("inline_data")
                    if inl:
                        return base64.b64decode(inl["data"])
                return None  # 텍스트만 옴
            # 에러: 429/5xx 면 백오프
            err = (d.get("error") or {})
            code = err.get("code")
            if code in (429, 500, 503):
                time.sleep(8 + attempt * 8); continue
            print("   ! API error:", json.dumps(err)[:200]); return None
        return None
    finally:
        os.unlink(bodyfile)

def main():
    items = list(targets())
    done = 0; skipped = 0; failed = []
    for i, (path, prompt) in enumerate(items, 1):
        # 이미 임베드(=PNG 래핑)된 파일이면 건너뛰기(재개)
        if path.exists() and "data:image/png;base64" in path.read_text(encoding="utf-8", errors="ignore"):
            skipped += 1; continue
        print(f"[{i}/{len(items)}] {path.relative_to(ASSETS)} ...", flush=True)
        png = generate(prompt)
        if not png:
            failed.append(str(path.relative_to(ASSETS))); print("   FAILED"); continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(wrap_svg(png), encoding="utf-8")
        done += 1
        print(f"   OK {len(png)//1024}KB", flush=True)
        time.sleep(1.5)  # 레이트리밋 여유
    print(f"\n=== 완료: 생성 {done} · 건너뜀 {skipped} · 실패 {len(failed)} ===")
    if failed:
        print("실패:", failed)

if __name__ == "__main__":
    main()
