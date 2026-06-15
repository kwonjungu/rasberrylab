/* 서보모터(출력) — angle(현재 각도°). 신호=D5(GPIO14). Servo 라이브러리 필요.
 * 실제 각도 명령은 commands/{id}/ 로 확장. 여기선 현재 각도 보고 */
#include "sensors/sensor_common.h"
#include <Servo.h>
#define SENSOR_NAME "angle"
#define PIN 14
static Servo _servo; static int _angle = 90;
void setup_sensor(){ _servo.attach(PIN); _servo.write(_angle); }
SensorReading read_sensor(){ return { (float)_angle, "deg", "good" }; }
int recommended_interval_ms(){ return 1000; }
