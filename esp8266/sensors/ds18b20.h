/* DS18B20 방수 온도 — temperature. D2(GPIO4). OneWire + DallasTemperature 필요 */
#include "sensors/sensor_common.h"
#include <OneWire.h>
#include <DallasTemperature.h>
#define SENSOR_NAME "temperature"
static OneWire _ow(4); static DallasTemperature _ds(&_ow);
void setup_sensor(){ _ds.begin(); }
SensorReading read_sensor(){ _ds.requestTemperatures(); float t=_ds.getTempCByIndex(0); return { t, "celsius", (t==-127)?"bad":"good" }; }
int recommended_interval_ms(){ return 1000; }
