/* 두드림(탭/노크) — tap(0/1). D5(GPIO14). 두드릴 때 순간 1 */
#include "sensors/sensor_common.h"
#define SENSOR_NAME "tap"
#define PIN 14
void setup_sensor(){ pinMode(PIN,INPUT); }
SensorReading read_sensor(){ return { (float)(digitalRead(PIN)?1:0), "bool", "good" }; }
int recommended_interval_ms(){ return 100; }
