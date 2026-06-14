#!/bin/bash
# Science AI Lab — ESP8266 펌웨어 굽기 (교사용)
# 사용: ./flash_script.sh <ESP_ID> <sensor> [포트]
#   예: ./flash_script.sh esp-01 dht11 /dev/ttyUSB0
# 요구: arduino-cli, esp8266 보드패키지, 라이브러리(PubSubClient, ArduinoJson, DHT 등)
set -e

ESP_ID="${1:-esp-01}"
SENSOR="${2:-dht11}"
PORT="${3:-/dev/ttyUSB0}"
FQBN="esp8266:esp8266:nodemcuv2"
HERE="$(cd "$(dirname "$0")" && pwd)"

if ! command -v arduino-cli >/dev/null; then
  echo "❌ arduino-cli 가 필요합니다. https://arduino.github.io/arduino-cli 참고"
  exit 1
fi
if [ ! -f "$HERE/lib/wifi_config.h" ]; then
  echo "❌ esp8266/lib/wifi_config.h 가 없습니다. wifi_config.h.example 를 복사해 작성하세요."
  exit 1
fi

# 임시 스케치 폴더 구성 (보드별 #define 치환)
BUILD="$(mktemp -d)/ScienceLabESP"
mkdir -p "$BUILD"
cp -r "$HERE/sensors" "$HERE/lib" "$BUILD/"
sed -e "s|#define ESP_ID .*|#define ESP_ID \"$ESP_ID\"|" \
    -e "s|#define SENSOR_INCLUDE .*|#define SENSOR_INCLUDE \"sensors/${SENSOR}.h\"|" \
    "$HERE/template.ino" > "$BUILD/ScienceLabESP.ino"

echo "==> 컴파일: $ESP_ID / $SENSOR"
arduino-cli compile --fqbn "$FQBN" "$BUILD"
echo "==> 업로드: $PORT"
arduino-cli upload -p "$PORT" --fqbn "$FQBN" "$BUILD"
echo "==> 완료. 시리얼 모니터: arduino-cli monitor -p $PORT -c baudrate=115200"
