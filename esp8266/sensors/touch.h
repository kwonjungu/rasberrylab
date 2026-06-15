/* 터치 센서(TTP223) — touch(0/1). D5(GPIO14). 닿으면 1 (액티브 하이) */
#include "sensors/sensor_common.h"
#define SENSOR_NAME "touch"
#define PIN 14
void setup_sensor(){ pinMode(PIN,INPUT); }
SensorReading read_sensor(){ return { (float)(digitalRead(PIN)?1:0), "bool", "good" }; }
int recommended_interval_ms(){ return 150; }
