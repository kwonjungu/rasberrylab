/* SMD RGB LED(출력, PWM) — led 상태(0/1, R 기준). R=D5(GPIO14), G=D6(GPIO12), B=D7(GPIO13) */
#include "sensors/sensor_common.h"
#define SENSOR_NAME "led"
#define R 14
#define G 12
#define B 13
void setup_sensor(){ pinMode(R,OUTPUT); pinMode(G,OUTPUT); pinMode(B,OUTPUT); digitalWrite(R,LOW); digitalWrite(G,LOW); digitalWrite(B,LOW); }
SensorReading read_sensor(){ return { (float)digitalRead(R), "bool", "good" }; }
int recommended_interval_ms(){ return 1000; }
