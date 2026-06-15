# Science AI Lab — 설치 & 운영 가이드 (Phase 6)

> 모든 코드는 작성·검증 완료. 아래 명령은 **Pi 콘솔(또는 SSH)에서 직접 실행**하세요.
> systemd 등록·키오스크·WiFi AP 전환은 sudo/재부팅이 필요합니다.

## 1. 설치 (한 줄)
```bash
cd /mnt/nvme/projects/science-ai
bash scripts/install.sh          # 패키지·venv·systemd·바탕화면 아이콘
bash scripts/first_boot.py       # 모둠 이름·교사 PIN·WiFi 설정
sudo reboot
```
재부팅하면: 백엔드·워밍·워치독 자동 기동 → 바탕화면 **[과학 실험실]** 아이콘 → 더블클릭 시 Chromium 키오스크.

## 2. 자동 기동 확인
```bash
systemctl status science-ai-backend science-ai-warmup science-ai-watchdog
curl -s localhost:8000/health
curl -s localhost:8000/api/admin/diagnose | python3 -m json.tool   # 종합 진단
```

## 3. WiFi AP (ESP 연결용, 선택) — ⚠️ SSH 끊길 수 있음, 콘솔에서
```bash
# network/README.md 참고
sudo cp network/hostapd.conf /etc/hostapd/hostapd.conf
sudo cp network/dnsmasq.conf /etc/dnsmasq.d/science-lab.conf
sudo cp network/mosquitto-lan.conf /etc/mosquitto/conf.d/science-lab.conf
sudo bash network/setup_ap.sh
sudo systemctl enable science-ai-ap
sudo reboot
```

## 4. 백업 자동화 (cron, 매일 자정)
```bash
( crontab -l 2>/dev/null; echo "0 0 * * * /mnt/nvme/projects/science-ai/scripts/backup.sh" ) | crontab -
```

## 5. 운영 명령
| 작업 | 명령 |
|---|---|
| 코드 갱신 | `bash scripts/update.sh` |
| 백업 | `bash scripts/backup.sh` |
| 복원 | `bash scripts/restore.sh <백업.tar.gz>` |
| 새 모둠 Pi | `bash scripts/clone-to-new-pi.sh B` |
| 제거(데이터 보존) | `bash scripts/uninstall.sh` |

## 6. 학생 보호 / 교사 해제
- 키오스크 + `student_lock.js`로 F11/F12/우클릭/새로고침/탭이동 차단.
- 우상단 🎓 → 교사 PIN 입력 → 브라우저 기능 복원. 30초 무입력 시 자동 학생 모드 복귀.
- 전원 버튼 long-press = 종료(짧게는 무시) — raspi-config에서 설정 권장.

## USB 직결 모드 (WiFi/IP 없이 — 권장 데모/단일 PC)

ESP를 USB 케이블로 Pi에 꽂고 데이터를 받는 경로. 네트워크 불필요.

```bash
# 1) 플래시 툴(최초 1회, 유저영역)
curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | BINDIR=/mnt/nvme/bin sh
export PATH=/mnt/nvme/bin:$PATH
export ARDUINO_DIRECTORIES_DATA=/mnt/nvme/arduino15 ARDUINO_DIRECTORIES_USER=/mnt/nvme/Arduino
arduino-cli config init --overwrite
arduino-cli config add board_manager.additional_urls https://arduino.esp8266.com/stable/package_esp8266com_index.json
arduino-cli core update-index && arduino-cli core install esp8266:esp8266
arduino-cli lib install "DHT sensor library"

# 2) 멀티포트 펌웨어 굽기 (한 번만! 이후 센서는 자유롭게 교체, 재플래시 불필요)
bash esp8266/flash_serial.sh multi

# (특정 센서 전용으로 굽고 싶으면)  bash esp8266/flash_serial.sh photoresistor
```

멀티포트 펌웨어: A0(아날로그) + D1/D5/D6/D7(디지털) + D2(DHT11 온습도)를 동시에 발행.
백엔드 `serial_reader`가 `/dev/ttyUSB0`를 자동으로 읽어 앱 대시보드에 띄운다.
포트 규칙 — 아날로그 센서→**A0**, 디지털 센서→**D5**, 온습도→**D2**.
