/* 소리 센서 — sound. A0 아날로그(고감도 모듈) */
#include "sensors/sensor_common.h"
#define SENSOR_NAME "sound"
void setup_sensor(){ pinMode(A0,INPUT); }
SensorReading read_sensor(){ return { (float)analogRead(A0), "raw", "good" }; }
int recommended_interval_ms(){ return 200; }
