/* 기본 온도 센서(아날로그) — temperature. A0. 상대값(raw) */
#include "sensors/sensor_common.h"
#define SENSOR_NAME "temperature"
void setup_sensor(){ pinMode(A0,INPUT); }
SensorReading read_sensor(){ return { (float)analogRead(A0), "raw", "good" }; }
int recommended_interval_ms(){ return 1000; }
