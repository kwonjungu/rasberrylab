/* Science AI Lab — ESP8266 USB 멀티포트 펌웨어 (한 번만 굽고, 센서는 자유롭게 교체)
 *
 * "센서 바꿀 때마다 다시 굽기"를 없애는 펌웨어. 보드의 여러 포트를 동시에 읽어
 * 각각 JSON 한 줄로 시리얼에 발행한다. 백엔드 serial_reader가 포트별로 분리해
 * 앱 대시보드에 여러 센서로 띄운다. WiFi/IP 불필요(USB 전용).
 *
 * 읽는 포트:
 *   A0          아날로그 0~1023  → 조도·소리·홀·토양·심박 등 모든 아날로그 센서 (A0는 1개뿐)
 *   D1,D5,D6,D7 디지털 0/1        → 버튼·리드·터치·기울기·IR·PIR 등 디지털 센서
 *   D2          DHT11 온습도      → 꽂혀 있으면 temperature/humidity, 없으면 자동 생략
 *   (부팅 영향 핀 D3/D4/D8, 인터럽트 없는 D0 은 안전상 제외)
 *
 * 센서 교체 절차: 그냥 포트에 꽂기만 하면 됨. 재플래시 불필요.
 *   - 아날로그 센서  → AO 핀을 A0 에
 *   - 디지털 센서    → DO/S 핀을 D1/D5/D6/D7 중 하나에
 *   - 온습도(DHT11)  → 신호핀을 D2 에
 *
 * 필요한 라이브러리: DHT sensor library by Adafruit (+ Adafruit Unified Sensor)
 */
#include <DHT.h>

#define DHT_PIN 4   // D2 (GPIO4)
DHT dht(DHT_PIN, DHT11);

struct DPin { const char* name; uint8_t gpio; };
DPin dpins[] = { {"D1", 5}, {"D5", 14}, {"D6", 12}, {"D7", 13} };
const int NDP = sizeof(dpins) / sizeof(dpins[0]);

unsigned long lastAnalog = 0, lastDigital = 0, lastDHT = 0, lastHB = 0;

void emit(const char* sensor, float value, const char* unit, const char* quality) {
  Serial.print("{\"type\":\"data\",\"sensor\":\"");
  Serial.print(sensor);
  Serial.print("\",\"value\":");
  Serial.print(value, 2);
  Serial.print(",\"unit\":\"");
  Serial.print(unit);
  Serial.print("\",\"quality\":\"");
  Serial.print(quality);
  Serial.println("\"}");
}

void setup() {
  Serial.begin(115200);
  delay(200);
  pinMode(A0, INPUT);
  for (int i = 0; i < NDP; i++) pinMode(dpins[i].gpio, INPUT_PULLUP);
  dht.begin();
  Serial.println("{\"type\":\"info\",\"board_type\":\"nodemcu-usb-multi\","
                 "\"ports\":[\"A0\",\"D1\",\"D5\",\"D6\",\"D7\",\"temperature\",\"humidity\"]}");
}

void loop() {
  unsigned long now = millis();

  if (now - lastAnalog > 500) {
    emit("A0", (float)analogRead(A0), "raw", "good");
    lastAnalog = now;
  }

  if (now - lastDigital > 500) {
    for (int i = 0; i < NDP; i++)
      emit(dpins[i].name, (float)(digitalRead(dpins[i].gpio) ? 1 : 0), "bool", "good");
    lastDigital = now;
  }

  if (now - lastDHT > 2500) {
    float t = dht.readTemperature();
    float h = dht.readHumidity();
    if (!isnan(t)) emit("temperature", t, "celsius", "good");
    if (!isnan(h)) emit("humidity", h, "percent", "good");
    lastDHT = now;
  }

  if (now - lastHB > 5000) {
    Serial.print("{\"type\":\"heartbeat\",\"uptime_s\":");
    Serial.print(now / 1000);
    Serial.println("}");
    lastHB = now;
  }
}
