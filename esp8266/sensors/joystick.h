/* 조이스틱 — x_raw(VRx). VRx=A0 아날로그, SW=D5(GPIO14) 버튼.
 * ESP8266 ADC 1개뿐이라 VRx만 발행, 버튼 눌림은 음수로 표시(-1) */
#include "sensors/sensor_common.h"
#define SENSOR_NAME "x_raw"
#define SW 14
void setup_sensor(){ pinMode(A0,INPUT); pinMode(SW,INPUT_PULLUP); }
SensorReading read_sensor(){
  if(digitalRead(SW)==LOW) return { -1.0f, "raw", "good" }; // 버튼 눌림
  return { (float)analogRead(A0), "raw", "good" };
}
int recommended_interval_ms(){ return 200; }
