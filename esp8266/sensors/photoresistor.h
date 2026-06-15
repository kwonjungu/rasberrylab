/* 조도(포토레지스터) — light. A0 아날로그. 밝을수록 값 변화 */
#include "sensors/sensor_common.h"
#define SENSOR_NAME "light"
void setup_sensor(){ pinMode(A0,INPUT); }
SensorReading read_sensor(){ return { (float)analogRead(A0), "raw", "good" }; }
int recommended_interval_ms(){ return 500; }
