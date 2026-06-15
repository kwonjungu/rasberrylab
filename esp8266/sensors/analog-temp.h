/* 아날로그 온도(서미스터) — temperature. A0 아날로그.
 * 보정 전 상대값(raw). 절대 ℃가 필요하면 dht11/ds18b20 사용 */
#include "sensors/sensor_common.h"
#define SENSOR_NAME "temperature"
void setup_sensor(){ pinMode(A0,INPUT); }
SensorReading read_sensor(){ return { (float)analogRead(A0), "raw", "good" }; }
int recommended_interval_ms(){ return 1000; }
