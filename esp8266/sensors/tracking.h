/* 라인 트래킹(적외선) — line(0/1). D5(GPIO14). 검은선 감지 시 1 (액티브 로우) */
#include "sensors/sensor_common.h"
#define SENSOR_NAME "line"
#define PIN 14
void setup_sensor(){ pinMode(PIN,INPUT); }
SensorReading read_sensor(){ return { (float)(digitalRead(PIN)==LOW?1:0), "bool", "good" }; }
int recommended_interval_ms(){ return 100; }
