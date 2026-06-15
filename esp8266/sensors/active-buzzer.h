/* 능동 부저(출력) — buzzer 상태(0/1). D6(GPIO12) */
#include "sensors/sensor_common.h"
#define SENSOR_NAME "buzzer"
#define PIN 12
void setup_sensor(){ pinMode(PIN,OUTPUT); digitalWrite(PIN,LOW); }
SensorReading read_sensor(){ return { (float)digitalRead(PIN), "bool", "good" }; }
int recommended_interval_ms(){ return 1000; }
