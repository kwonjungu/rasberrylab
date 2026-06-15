/* DC 모터(출력, 드라이버 경유) — motor 상태(0/1, IN1 기준). IN1=D5(GPIO14), IN2=D6(GPIO12).
 * ⚠ 모터 드라이버 필수·ESP 직결 금지 */
#include "sensors/sensor_common.h"
#define SENSOR_NAME "motor"
#define IN1 14
#define IN2 12
void setup_sensor(){ pinMode(IN1,OUTPUT); pinMode(IN2,OUTPUT); digitalWrite(IN1,LOW); digitalWrite(IN2,LOW); }
SensorReading read_sensor(){ return { (float)digitalRead(IN1), "bool", "good" }; }
int recommended_interval_ms(){ return 1000; }
