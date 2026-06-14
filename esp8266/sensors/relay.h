/* 릴레이(출력) — relay 상태 보고만(value=현재상태). D6(GPIO12).
 * ⚠ 220V 금지·저전압만·교사 동반. 실제 on/off는 commands/{id}/led 등으로 확장 */
#include "sensors/sensor_common.h"
#define SENSOR_NAME "relay"
#define PIN 12
void setup_sensor(){ pinMode(PIN,OUTPUT); digitalWrite(PIN,LOW); }
SensorReading read_sensor(){ return { (float)digitalRead(PIN), "bool", "good" }; }
int recommended_interval_ms(){ return 1000; }
