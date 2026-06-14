/* 조도(LDR) — light. A0 아날로그 */
#include "sensors/sensor_common.h"
#define SENSOR_NAME "light"
void setup_sensor(){ pinMode(A0,INPUT); }
SensorReading read_sensor(){ return { (float)analogRead(A0), "raw", "good" }; }
int recommended_interval_ms(){ return 500; }
