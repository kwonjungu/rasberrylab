/* 수동 부저(출력, PWM 음정) — buzzer 상태(0/1). D6(GPIO12).
 * 음정은 tone()으로 확장. 여기선 출력 상태만 보고 */
#include "sensors/sensor_common.h"
#define SENSOR_NAME "buzzer"
#define PIN 12
void setup_sensor(){ pinMode(PIN,OUTPUT); digitalWrite(PIN,LOW); }
SensorReading read_sensor(){ return { (float)digitalRead(PIN), "bool", "good" }; }
int recommended_interval_ms(){ return 1000; }
