/* HC-SR04 초음파 거리 — distance_cm. Trig=D5(GPIO14), Echo=D6(GPIO12, 분압 필수) */
#include "sensors/sensor_common.h"
#define SENSOR_NAME "distance_cm"
#define TRIG 14
#define ECHO 12
void setup_sensor(){ pinMode(TRIG,OUTPUT); pinMode(ECHO,INPUT); }
SensorReading read_sensor(){
  digitalWrite(TRIG,LOW); delayMicroseconds(2);
  digitalWrite(TRIG,HIGH); delayMicroseconds(10); digitalWrite(TRIG,LOW);
  long us=pulseIn(ECHO,HIGH,30000); float cm=us*0.0343/2.0;
  return { cm, "cm", (us==0)?"bad":"good" };
}
int recommended_interval_ms(){ return 300; }
