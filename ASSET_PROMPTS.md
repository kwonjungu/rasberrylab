# 🎨 Science AI Lab — 에셋 생성 프롬프트 설계서

> 외부 자문(디자인 검수) 산출물. 현재 앱에는 **즉시 동작하는 SVG 에셋**이 이미 들어가 있습니다
> (`frontend/assets/`). 이 문서는 그 SVG들을 **고품질 일러스트(래스터)** 로 업그레이드하려는
> 사용자를 위한 이미지 생성 프롬프트 모음입니다. Midjourney / DALL·E 3 / Stable Diffusion 공용.
>
> 대상: 초등 3~6학년(만 9~12세) · 키오스크 1m 가독성 · 한국 과학교실.

---

## 0. 공통 아트 디렉션 (모든 프롬프트 앞에 붙이기)

```
flat vector illustration for a Korean elementary school science app,
friendly rounded shapes, soft pastel palette (sky blue #3b82f6, mint green #22c55e,
warm amber #f59e0b, soft pink #ec4899), thick clean outlines, gentle drop shadows,
high readability from 1 meter, cheerful and safe, kid-friendly, no text,
centered subject, generous padding, white-ish background, crisp edges
```

**네거티브(공통)**
```
--no text, watermark, signature, realistic photo, horror, scary, sharp weapons,
clutter, low contrast, dark gloomy colors, tiny details, distorted hands, extra fingers
```

**도구별 파라미터**
- Midjourney: ` --style raw --ar 3:2 --v 6.1`  (아이콘류는 `--ar 1:1`, 마스코트 turnaround는 `--ar 16:9`)
- DALL·E 3: 프롬프트 끝에 `, simple flat illustration, transparent or solid pastel background`
- SD(권장 모델 기준): Steps 28~35, CFG 6~7, sampler DPM++ 2M Karras, 사이즈 1024×683(3:2) 또는 1024×1024.
  로고/텍스트 금지 위해 LoRA "flat-vector" 류 권장.

---

## 1. 마스코트 "라비(Labi)" — 앱의 얼굴 🤖

세계관: 실험실 도우미 로봇. 둥근 파란 몸, 머리 위 빛나는 안테나, 청록색(시안) 눈,
분홍 볼터치. 항상 호기심 많고 다정함. **일관성 유지가 가장 중요** → 한 번 turnaround를 뽑고
그 이미지를 레퍼런스로 표정/포즈 변형.

### 1-1. 캐릭터 시트(turnaround)
```
[공통] character turnaround sheet of "Labi", a cute friendly lab-assistant robot mascot,
rounded sky-blue body and head, glowing cyan antenna on top, big glowing cyan eyes,
pink cheek blush, tiny rounded arms, holding a small magnifying glass,
front / side / back views, consistent design, mascot logo style --ar 16:9
```

### 1-2. 표정·포즈 변형 (각각 별도 생성, 라비 레퍼런스 첨부)
| 파일 제안 | 용도 | 프롬프트 핵심 |
|---|---|---|
| `labi-wave` | 지도/인사 | `waving one hand, warm welcoming smile` |
| `labi-cheer` | 미션 클리어 | `both arms up celebrating, sparkles and confetti, holding a gold medal` |
| `labi-think` | 힌트/막힘 | `tilting head, one hand on chin, thinking, small question mark` |
| `labi-point` | 브리핑/안내 | `pointing forward with a friendly grin, presenting` |
| `labi-safety` | 안전 복창 | `wearing tiny safety goggles, raising hand, reassuring` |
| `labi-sensor` | 센서 연결 | `holding a jumper wire and a small sensor chip, helpful` |
| `labi-sleep` | 대기/끊김 | `eyes closed, small "zzz", resting` |

---

## 2. 월드(학년 구역) 키 비주얼 5종 🗺

지도 배경/배너용 풍경. 각 구역 분위기:

```
[g3] "Curiosity Village" — a sunny green meadow with little science cottages,
floating curiosity sparkles, beginner-friendly, soft green theme

[g4] "Explorer Hills" — rolling hills with a telescope and a winding discovery path,
adventurous, indigo/blue theme

[g5] "Experiment Valley" — a valley lab with bubbling beakers and gentle electric sparks,
energetic, amber theme

[g6] "Discovery Peak" — a tall friendly mountain summit with a rocket and flags,
triumphant, pink/magenta theme

[fusion] "Challenge Base" — a small futuristic space station with robots and circuits,
high-tech but cute, cyan theme
```
공통 접미: `wide game level-select map background, no characters, no text`

### 2-1. 구역 배지(엠블럼) — 1:1
```
shield emblem badge, glossy, ribbon banner, single centered icon
( 🌱 / 🔭 / ⚡ / 🚀 / 🛰 ), thick white border, game UI badge --ar 1:1
```

---

## 3. 스테이지 아이콘 14종 (실험별) — 1:1

지도 위 스테이지 버튼/브리핑 히어로. 각 실험 1개씩, **둥근 배지 안 단일 오브젝트**.

| 실험 | 아이콘 핵심 프롬프트 |
|---|---|
| 자석 세기 거리별 측정 | `red horseshoe magnet with magnetic field arcs and a ruler` |
| 자석 소리 크기(박수) | `two clapping hands with sound waves` |
| 얼음 녹는 온도 | `ice cube with a thermometer and a water drop` |
| 그림자 빛 차단 | `a hand casting a soft shadow under a glowing lamp` |
| 진동 흔들림 측정 | `a shaking table with a small volcano and motion lines` |
| 단열 재료 비교 | `a warm cup wrapped in a scarf, steam rising` |
| 자동 거리-속도 측정 | `a cute car with an ultrasonic sensor and a stopwatch` |
| RC카 가속도 | `a small RC race car speeding with motion blur` |
| 자동 전등 | `a light bulb turning on in the dark with a sensor` |
| 심장박동 측정 | `a red heart with a pulse line and a running shoe` |
| 빛 색 섞기 | `red green blue light beams mixing into a rainbow` |
| 자동문 시스템 | `a sliding automatic door opening with a motion sensor` |
| 자율주행차 | `a friendly robot car following a line, avoiding a cone` |
| 스마트 화분 | `a potted sprout with a water drop and a moisture sensor` |
공통 접미: `inside a soft rounded badge, single object, game stage icon --ar 1:1`

---

## 4. 단계 삽화 34종 (실험 진행 화면) — 3:2

현재 SVG가 들어있는 항목들. 파일명 = `frontend/assets/steps/<key>.svg` → 같은 key로 PNG 교체.
각 장면은 **손/도구가 한 동작을 하는 모습** + 라비가 옆에서 돕는 구도 권장.

```
linear-hall-plug   : kid hands plugging a hall sensor into a breadboard, Labi pointing
magnet-1cm         : a magnet held 1cm from a sensor, glowing field, ruler showing 1cm
magnet-far         : a magnet moved far from a sensor, fading field arcs, double arrow
sound-quiet        : a quiet classroom, finger on lips, small sound meter low
sound-clap         : hands clapping loudly, big sound waves, meter spiking high
ice-sensor         : placing a thermometer probe into an ice cup
ice-melt           : ice slowly melting into water, droplets, thermometer
light-bright       : a bright lamp shining on a light sensor, sunny
light-block        : a hand blocking light, casting shadow on a sensor
shock-buzzer       : wiring a shock sensor to a buzzer on a breadboard
shake-table        : hands shaking a desk, a small model, wobble lines
warm-water         : pouring warm water into a cup, steam
insulation         : wrapping a cup with wool/foil, comparing two cups
ultrasonic-setup   : mounting an HC-SR04 ultrasonic sensor facing a toy car
car-roll           : a toy car rolling down a gentle ramp
calc-speed         : a kid with a stopwatch and a ruler computing speed, "distance ÷ time"
auto-light-wire    : wiring an LED + light sensor circuit on a breadboard
cover-sensor       : covering a sensor with a hand/box to test it
heartbeat-rest     : a child sitting calmly with a pulse sensor on a fingertip
heartbeat-exercise : a child jumping/running then checking pulse
rgb-red            : an RGB LED glowing red
rgb-mix            : an RGB LED mixing colors into white/rainbow
rc-build           : assembling a small RC car with tools
rc-run             : an RC car racing on a track
rc-crash           : an RC car gently bumping a soft wall, impact stars
door-build         : building a model automatic door with a servo
door-open          : a person approaching and the door sliding open
self-driving-build : assembling a robot car with line/obstacle sensors
follow-line        : a robot car following a black line on white floor
avoid-obstacle     : a robot car turning to avoid an orange cone
soil-sensor        : inserting a moisture sensor into a flower pot's soil
auto-water         : a tiny pump watering a sprout automatically
```
공통 접미(각 줄 뒤): `, flat vector scene, Labi the blue robot helping, cheerful --ar 3:2`

---

## 5. 온보딩 삽화 2종 — 3:2
```
breadboard-power : connecting a battery/USB power to a breadboard power rail,
                   red(+) and black(–) rails highlighted, Labi explaining
dht11-connect    : connecting a DHT11 temp/humidity sensor to a breadboard with 3 wires
```

## 6. 센서 배선 다이어그램 42종 — 3:2 (정보 전달용)
> 일러스트보다 **명확한 도식**이 중요 → 사실 SVG가 더 적합(이미 생성됨).
> 굳이 래스터로 만들려면:
```
clean wiring diagram, top-down breadboard, a labeled <SENSOR NAME> module,
three jumper wires color-coded red(VCC) black(GND) yellow(signal),
infographic style, flat, high contrast, minimal --ar 3:2
```
`<SENSOR NAME>` 에 각 센서명(DHT11, HC-SR04, Linear Hall, …) 대입. (목록: `frontend/assets/wiring/` 파일명)

---

## 7. 배경 / 분위기
```
map-sky      : soft gradient sky with fluffy clouds and a tiny satellite,
               wide seamless game background, no characters
mission-bg   : very subtle light-blue lab background, lots of empty space (UI overlays on top)
safety-bg    : warm friendly safety-briefing backdrop, soft amber, goggles & gloves motif
```

## 8. UI 요소 / 이펙트
```
star-filled / star-empty : a plump golden star / a soft gray outline star, game rating, 1:1
rank-medal-1..5          : bronze→silver→gold→platinum→rainbow medal with ribbon, 1:1
                           ( 새싹🌱 / 꼬마🔍 / 주니어🧪 / 수석🥽 / 마스터🏆 단계 )
button-go                : a big friendly green "start" pill button, glossy, 3D press
confetti-burst           : colorful confetti and sparkles burst, transparent background
progress-rocket          : a small rocket used as a progress bar marker
help-bell                : a friendly orange bell icon (도움요청), 1:1
```

## 9. (선택) 사운드/보이스 디자인 — 오디오 생성 도구용 프롬프트
> ElevenLabs/Suno 등. 짧고 부드럽게, 놀라지 않게.
```
correct      : "soft cheerful chime, two notes up, gentle, kids game success"
clear        : "short triumphant fanfare, playful, marimba + bells, 2 seconds"
help         : "gentle attention ding, warm, non-alarming"
tap          : "soft bubble pop UI tap"
labi-voice   : "friendly warm child-companion robot voice, Korean, slightly bright, calm pace"
```

---

## 10. 교체 방법 (요약)
1. 위 프롬프트로 이미지를 만들고 같은 **파일명**(확장자만 .png/.webp)으로 저장.
2. `frontend/assets/steps|wiring|onboarding|mascot|region/` 에 덮어쓰기.
3. 데이터의 `image_path` 가 `.svg` 를 가리키면, 새 파일을 `.svg` 와 같은 이름의 `.png` 로 두고
   `backend/data/experiments.json` 의 확장자만 일괄 변경(또는 SVG 안에 `<image>` 로 임베드).
4. 마스코트 교체 시 `frontend/story.js` 의 `mascot.img` / `mascot.cheer` 경로만 맞추면 끝.

> 팁: 일관성 = 같은 **시드/스타일 레퍼런스**를 모든 컷에 재사용. 라비는 항상 같은 turnaround를
> 레퍼런스로 첨부해 색·비례를 고정하세요.
