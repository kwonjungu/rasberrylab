#!/bin/bash
# Science AI Lab — USB 시리얼 펌웨어 굽기 (라즈베리파이에서 1줄 실행)
#
#   bash esp8266/flash_serial.sh <센서id> [포트]
#   예) bash esp8266/flash_serial.sh dht11
#       bash esp8266/flash_serial.sh photoresistor /dev/ttyUSB0
#
# 하는 일: 백엔드 정지(포트 해제) → 해당 센서 헤더로 컴파일+업로드 → 백엔드 재기동.
# arduino-cli + esp8266 코어가 /mnt/nvme 에 설치돼 있다고 가정.
set -e

SENSOR="${1:?사용법: flash_serial.sh <센서id> [포트]  (예: dht11)}"
PORT="${2:-/dev/ttyUSB0}"
FQBN="esp8266:esp8266:nodemcuv2"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"           # 프로젝트 루트
HDR="$ROOT/esp8266/sensors/$SENSOR.h"

export PATH="/mnt/nvme/bin:$PATH"
export ARDUINO_DIRECTORIES_DATA=/mnt/nvme/arduino15
export ARDUINO_DIRECTORIES_USER=/mnt/nvme/Arduino

# 1) 격리된 빌드 스케치 구성
BUILD=/tmp/sci_serial
rm -rf "$BUILD"; mkdir -p "$BUILD"
if [ "$SENSOR" = "multi" ]; then
  # 멀티포트 펌웨어 — 한 번만 굽고 센서는 자유 교체(재플래시 불필요). 권장 기본값.
  cp "$ROOT/esp8266/firmware_multi.ino" "$BUILD/sci_serial.ino"
  echo "🛠  멀티포트 펌웨어  포트=$PORT  (A0 + D1/D5/D6/D7 + DHT11@D2 동시 수신)"
else
  [ -f "$HDR" ] || { echo "❌ 센서 헤더 없음: $HDR"; echo "가능: multi  $(cd "$ROOT/esp8266/sensors" && ls *.h | sed 's/.h//' | tr '\n' ' ')"; exit 1; }
  sed "s#\"sensors/[a-zA-Z0-9_-]*\.h\"#\"sensors/$SENSOR.h\"#" \
      "$ROOT/esp8266/template_serial.ino" > "$BUILD/sci_serial.ino"
  cp -r "$ROOT/esp8266/sensors" "$BUILD/"
  echo "🛠  센서=$SENSOR  포트=$PORT  →  $(grep -m1 SENSOR_INCLUDE "$BUILD/sci_serial.ino")"
fi

# 2) 백엔드 정지 → 포트 해제 (User=kwon, Restart=on-failure 라 정상종료 시 재기동 안 함)
MAINPID=$(systemctl show -p MainPID --value science-ai-backend 2>/dev/null || echo 0)
if [ "$MAINPID" != "0" ]; then
  echo "⏸  백엔드 정지(PID $MAINPID)"; kill -TERM "$MAINPID" 2>/dev/null || true
  for _ in $(seq 1 10); do kill -0 "$MAINPID" 2>/dev/null || break; sleep 1; done
fi

# 3) 컴파일 + 업로드 (스케치 루트를 include 경로로)
arduino-cli compile --upload -p "$PORT" -b "$FQBN" \
  --build-property "build.extra_flags=-I{build.source.path}" "$BUILD"

# 4) 백엔드 재기동
echo "▶  백엔드 재기동"
sudo -n systemctl start science-ai-backend
echo "✅ 완료 — '$SENSOR' 펌웨어가 USB로 값을 보냅니다. 앱 대시보드에서 확인하세요."
