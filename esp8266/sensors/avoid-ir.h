/* 장애물 감지(적외선) — obstacle(0/1). D5(GPIO14). 장애물 있으면 1 (액티브 로우) */
#include "sensors/sensor_common.h"
#define SENSOR_NAME "obstacle"
#define PIN 14
void setup_sensor(){ pinMode(PIN,INPUT); }
SensorReading read_sensor(){ return { (float)(digitalRead(PIN)==LOW?1:0), "bool", "good" }; }
int recommended_interval_ms(){ return 200; }
