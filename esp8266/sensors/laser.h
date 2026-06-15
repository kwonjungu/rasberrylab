/* 레이저 발광(출력) — laser 상태(0/1). D6(GPIO12).
 * ⚠ 눈 조준 금지·교사 동반. 실제 점멸은 commands/{id}/ 로 확장 */
#include "sensors/sensor_common.h"
#define SENSOR_NAME "laser"
#define PIN 12
void setup_sensor(){ pinMode(PIN,OUTPUT); digitalWrite(PIN,LOW); }
SensorReading read_sensor(){ return { (float)digitalRead(PIN), "bool", "good" }; }
int recommended_interval_ms(){ return 1000; }
