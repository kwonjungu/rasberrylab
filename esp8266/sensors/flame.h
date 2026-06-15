/* 화염 감지 — flame(0/1). D5(GPIO14). 불꽃 감지 시 1 (DO 액티브 로우) */
#include "sensors/sensor_common.h"
#define SENSOR_NAME "flame"
#define PIN 14
void setup_sensor(){ pinMode(PIN,INPUT); }
SensorReading read_sensor(){ return { (float)(digitalRead(PIN)==LOW?1:0), "bool", "good" }; }
int recommended_interval_ms(){ return 300; }
