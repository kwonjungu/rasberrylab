/* 토양 습도 — moisture. A0 아날로그. 젖을수록 값 변화(상대값) */
#include "sensors/sensor_common.h"
#define SENSOR_NAME "moisture"
void setup_sensor(){ pinMode(A0,INPUT); }
SensorReading read_sensor(){ return { (float)analogRead(A0), "raw", "good" }; }
int recommended_interval_ms(){ return 1000; }
