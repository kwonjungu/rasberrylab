/* Science AI Lab — ESP8266 펌웨어 템플릿 (결정적)
 *
 * LLM이 매번 새로 쓰지 않는다. 교사가 아래 두 줄만 바꿔서 보드별로 굽는다:
 *   - ESP_ID        : 보드 고유 이름 (스티커와 일치, 예 "esp-01")
 *   - SENSOR_INCLUDE: 사용할 센서 헤더 경로
 *
 * 필요한 라이브러리(Arduino IDE / arduino-cli):
 *   ESP8266 보드패키지, PubSubClient, ArduinoJson, (센서별: DHT sensor library 등)
 *
 * 동작: WiFi 자동연결 → mDNS로 science-lab.local 해석 → MQTT 연결 →
 *       센서값 발행 + 5초 하트비트 + LED 상태표시. 끊기면 자동 재연결.
 */
#include <ESP8266WiFi.h>
#include <ESP8266mDNS.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

#include "lib/wifi_config.h"   // wifi_config.h.example 를 복사해 작성

// ===== 보드별 설정 (여기만 수정) =====
#define ESP_ID "esp-01"
#define SENSOR_INCLUDE "sensors/dht11.h"
// =====================================

#include SENSOR_INCLUDE        // setup_sensor / read_sensor / SENSOR_NAME / recommended_interval_ms 제공

#define MQTT_BROKER_HOST "science-lab.local"   // mDNS. 실패 시 AP 게이트웨이로 폴백
#define MQTT_BROKER_FALLBACK_IP "192.168.50.1" // Pi AP 고정 IP
#define MQTT_PORT 1883
#define LED_PIN LED_BUILTIN
#define TOPIC_BASE "science-lab/sensors/"

WiFiClient espClient;
PubSubClient mqtt(espClient);

unsigned long lastPublish = 0;
unsigned long lastHeartbeat = 0;
unsigned long lastBlink = 0;
IPAddress brokerIp;

void blink(int period) {
  if (millis() - lastBlink > (unsigned long)period) {
    digitalWrite(LED_PIN, !digitalRead(LED_PIN));
    lastBlink = millis();
  }
}

void connectWifi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
    blink(200);            // 연결 중: 빠른 깜빡
    delay(50);
  }
  brokerIp = MQTT_BROKER_FALLBACK_IP;
  if (MDNS.begin(ESP_ID)) {
    // science-lab.local 해석 시도
    IPAddress resolved = MDNS.queryHost("science-lab");
    if (resolved != IPAddress(0, 0, 0, 0)) brokerIp = resolved;
  }
}

void publishInfo() {
  StaticJsonDocument<128> doc;
  doc["board_type"] = "nodemcu";
  doc["sensor"] = SENSOR_NAME;
  char buf[128]; size_t n = serializeJson(doc, buf);
  mqtt.publish((String(TOPIC_BASE) + ESP_ID + "/info").c_str(), (uint8_t*)buf, n, true);
}

void connectMqtt() {
  while (!mqtt.connected()) {
    blink(500);            // MQTT 연결 중: 보통 깜빡
    mqtt.setServer(brokerIp, MQTT_PORT);
    if (mqtt.connect(ESP_ID)) {
      publishInfo();
      mqtt.subscribe((String("science-lab/commands/") + ESP_ID + "/#").c_str());
    } else {
      delay(2000);         // 지수 백오프 단순화
    }
  }
}

void onCommand(char* topic, byte* payload, unsigned int len) {
  String t = String(topic);
  if (t.endsWith("/reset")) ESP.restart();
  // /led, /sample_rate 등은 필요 시 확장
}

void setup() {
  pinMode(LED_PIN, OUTPUT);
  Serial.begin(115200);
  setup_sensor();
  connectWifi();
  mqtt.setCallback(onCommand);
  connectMqtt();
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) connectWifi();
  if (!mqtt.connected()) connectMqtt();
  mqtt.loop();
  MDNS.update();

  digitalWrite(LED_PIN, LOW);  // 모두 정상: 켜둠(액티브 로우)

  unsigned long now = millis();
  if (now - lastPublish > (unsigned long)recommended_interval_ms()) {
    SensorReading r = read_sensor();
    StaticJsonDocument<128> doc;
    doc["ts"] = now / 1000;
    doc["value"] = r.value;
    doc["unit"] = r.unit;
    doc["quality"] = r.quality;
    char buf[128]; size_t n = serializeJson(doc, buf);
    mqtt.publish((String(TOPIC_BASE) + ESP_ID + "/data/" + SENSOR_NAME).c_str(), (uint8_t*)buf, n);
    lastPublish = now;
  }

  if (now - lastHeartbeat > 5000) {
    StaticJsonDocument<96> doc;
    doc["ts"] = now / 1000;
    doc["rssi"] = WiFi.RSSI();
    doc["uptime_s"] = now / 1000;
    doc["free_heap"] = ESP.getFreeHeap();
    char buf[96]; size_t n = serializeJson(doc, buf);
    mqtt.publish((String(TOPIC_BASE) + ESP_ID + "/heartbeat").c_str(), (uint8_t*)buf, n);
    lastHeartbeat = now;
  }
}
