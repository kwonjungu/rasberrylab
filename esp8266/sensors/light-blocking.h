/* 광 차단(포토 인터럽터) — blocked(0/1). D5(GPIO14). 빛이 가려지면 1 */
#include "sensors/sensor_common.h"
#define SENSOR_NAME "blocked"
#define PIN 14
void setup_sensor(){ pinMode(PIN,INPUT); }
SensorReading read_sensor(){ return { (float)(digitalRead(PIN)==LOW?1:0), "bool", "good" }; }
int recommended_interval_ms(){ return 200; }
