/* 충격/진동(SW-420) — shock(0/1). D5(GPIO14) 디지털 */
#include "sensors/sensor_common.h"
#define SENSOR_NAME "shock"
#define PIN 14
void setup_sensor(){ pinMode(PIN,INPUT); }
SensorReading read_sensor(){ return { (float)(digitalRead(PIN)?1:0), "bool", "good" }; }
int recommended_interval_ms(){ return 200; }
