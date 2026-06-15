/* 소형 소리 센서(디지털) — sound(0/1). D5(GPIO14). 임계 이상 소리 시 1 */
#include "sensors/sensor_common.h"
#define SENSOR_NAME "sound"
#define PIN 14
void setup_sensor(){ pinMode(PIN,INPUT); }
SensorReading read_sensor(){ return { (float)(digitalRead(PIN)?1:0), "bool", "good" }; }
int recommended_interval_ms(){ return 100; }
