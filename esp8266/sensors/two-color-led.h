/* 2색 LED(출력) — led 상태(0/1, S1 기준). S1=D5(GPIO14), S2=D6(GPIO12) */
#include "sensors/sensor_common.h"
#define SENSOR_NAME "led"
#define S1 14
#define S2 12
void setup_sensor(){ pinMode(S1,OUTPUT); pinMode(S2,OUTPUT); digitalWrite(S1,LOW); digitalWrite(S2,LOW); }
SensorReading read_sensor(){ return { (float)digitalRead(S1), "bool", "good" }; }
int recommended_interval_ms(){ return 1000; }
