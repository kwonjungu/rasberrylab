/* 홀 자기 스위치 — magnet(0/1). D5(GPIO14), 내부 풀업. 자석 근접 시 1 */
#include "sensors/sensor_common.h"
#define SENSOR_NAME "magnet"
#define PIN 14
void setup_sensor(){ pinMode(PIN,INPUT_PULLUP); }
SensorReading read_sensor(){ return { (float)(digitalRead(PIN)==LOW?1:0), "bool", "good" }; }
int recommended_interval_ms(){ return 200; }
