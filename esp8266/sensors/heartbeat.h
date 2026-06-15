/* 심박(펄스) 센서 — pulse. A0 아날로그. 파형 raw(심박수 계산은 백엔드에서) */
#include "sensors/sensor_common.h"
#define SENSOR_NAME "pulse"
void setup_sensor(){ pinMode(A0,INPUT); }
SensorReading read_sensor(){ return { (float)analogRead(A0), "raw", "good" }; }
int recommended_interval_ms(){ return 50; }
