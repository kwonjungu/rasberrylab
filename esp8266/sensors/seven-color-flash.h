/* 7색 자동 점멸 LED(출력) — led 상태(0/1). D5(GPIO14) */
#include "sensors/sensor_common.h"
#define SENSOR_NAME "led"
#define PIN 14
void setup_sensor(){ pinMode(PIN,OUTPUT); digitalWrite(PIN,LOW); }
SensorReading read_sensor(){ return { (float)digitalRead(PIN), "bool", "good" }; }
int recommended_interval_ms(){ return 1000; }
