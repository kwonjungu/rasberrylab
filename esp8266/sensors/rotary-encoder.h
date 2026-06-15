/* 로터리 엔코더 — position(누적 회전수). CLK=D5(GPIO14), DT=D6(GPIO12), SW=D7(GPIO13).
 * 인터럽트로 위치 누적, 버튼 누르면 0으로 리셋 */
#include "sensors/sensor_common.h"
#define SENSOR_NAME "position"
#define CLK 14
#define DT 12
#define SW 13
static volatile long _pos = 0;
static int _lastClk = HIGH;
void IRAM_ATTR _onClk(){
  int clk = digitalRead(CLK);
  if(clk != _lastClk && clk == LOW){ _pos += (digitalRead(DT) != clk) ? 1 : -1; }
  _lastClk = clk;
}
void setup_sensor(){
  pinMode(CLK,INPUT_PULLUP); pinMode(DT,INPUT_PULLUP); pinMode(SW,INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(CLK), _onClk, CHANGE);
}
SensorReading read_sensor(){
  if(digitalRead(SW)==LOW) _pos = 0;        // 버튼=리셋
  return { (float)_pos, "count", "good" };
}
int recommended_interval_ms(){ return 200; }
