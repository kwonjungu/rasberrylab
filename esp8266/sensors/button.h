/* 버튼 — button(0/1). D5(GPIO14), 내부 풀업 */
#include "sensors/sensor_common.h"
#define SENSOR_NAME "button"
#define PIN 14
void setup_sensor(){ pinMode(PIN,INPUT_PULLUP); }
SensorReading read_sensor(){ return { (float)(digitalRead(PIN)==LOW?1:0), "bool", "good" }; }
int recommended_interval_ms(){ return 200; }
