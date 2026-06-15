/* 매직 라이트 컵 LED(출력, PWM) — led 상태(0/1). D5(GPIO14).
 * 한 쌍 사용 시 다른 쪽은 tilt(기울기 입력)로 구성 */
#include "sensors/sensor_common.h"
#define SENSOR_NAME "led"
#define PIN 14
void setup_sensor(){ pinMode(PIN,OUTPUT); digitalWrite(PIN,LOW); }
SensorReading read_sensor(){ return { (float)digitalRead(PIN), "bool", "good" }; }
int recommended_interval_ms(){ return 1000; }
