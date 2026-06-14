/* DHT11 온습도 — 대표값은 온도(temperature). D2(GPIO4). DHT 라이브러리 필요 */
#include "sensors/sensor_common.h"
#include <DHT.h>
#define SENSOR_NAME "temperature"
static DHT _dht(4, DHT11);
void setup_sensor(){ _dht.begin(); }
SensorReading read_sensor(){ float t=_dht.readTemperature(); return { isnan(t)?0:t, "celsius", isnan(t)?"bad":"good" }; }
int recommended_interval_ms(){ return 2000; }
