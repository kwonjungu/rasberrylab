/* Science AI Lab — ESP8266 펌웨어 (USB 시리얼 전용, WiFi/MQTT 없음)
 *
 * USB 케이블만으로 라즈베리파이에 센서값을 보낸다. 네트워크/IP 불필요.
 * 백엔드의 serial_reader 가 /dev/ttyUSB0 에서 아래 JSON 줄을 읽어 처리한다.
 *
 * 교사는 아래 SENSOR_INCLUDE 한 줄만 보드에 맞게 바꿔서 굽는다.
 * 센서 헤더(read_sensor/setup_sensor/SENSOR_NAME/recommended_interval_ms)는
 * WiFi 펌웨어(template.ino)와 100% 공유한다.
 *
 * 출력 형식(개행 구분 JSON, 115200 baud):
 *   {"type":"info","sensor":"temperature","board_type":"nodemcu-usb"}
 *   {"type":"data","sensor":"temperature","value":22.4,"unit":"celsius","quality":"good"}
 *   {"type":"heartbeat","uptime_s":12}
 */

// ===== 보드별 설정 (여기만 수정) =====
#define SENSOR_INCLUDE "sensors/dht11.h"
// =====================================

#include SENSOR_INCLUDE   // setup_sensor / read_sensor / SENSOR_NAME / recommended_interval_ms

unsigned long lastPublish = 0;
unsigned long lastHeartbeat = 0;

void setup() {
  Serial.begin(115200);
  delay(200);
  setup_sensor();
  // 보드 식별 정보 1회 발행 → 백엔드가 활성 센서로 등록
  Serial.print("{\"type\":\"info\",\"sensor\":\"");
  Serial.print(SENSOR_NAME);
  Serial.println("\",\"board_type\":\"nodemcu-usb\"}");
}

void loop() {
  unsigned long now = millis();

  if (now - lastPublish > (unsigned long)recommended_interval_ms()) {
    SensorReading r = read_sensor();
    Serial.print("{\"type\":\"data\",\"sensor\":\"");
    Serial.print(SENSOR_NAME);
    Serial.print("\",\"value\":");
    Serial.print(r.value, 3);
    Serial.print(",\"unit\":\"");
    Serial.print(r.unit);
    Serial.print("\",\"quality\":\"");
    Serial.print(r.quality);
    Serial.println("\"}");
    lastPublish = now;
  }

  if (now - lastHeartbeat > 5000) {
    Serial.print("{\"type\":\"heartbeat\",\"uptime_s\":");
    Serial.print(now / 1000);
    Serial.println("}");
    lastHeartbeat = now;
  }
}
