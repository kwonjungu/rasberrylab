# Science AI Lab — 네트워크 설정 (Pi WiFi AP + MQTT LAN)

> ⚠️ **콘솔(키보드+모니터)에서 실행하세요.** Pi의 WiFi를 AP 모드로 바꾸면
> 현재 WiFi 기반 SSH 연결이 끊깁니다. 이더넷이나 직접 콘솔이 필요합니다.
> 이 폴더의 파일은 **준비된 설정**이며, 자동 적용되지 않습니다.

## 적용 순서 (콘솔에서)
```bash
sudo apt install -y hostapd dnsmasq
sudo cp network/hostapd.conf   /etc/hostapd/hostapd.conf
sudo cp network/dnsmasq.conf   /etc/dnsmasq.d/science-lab.conf
sudo cp network/mosquitto-lan.conf /etc/mosquitto/conf.d/science-lab.conf
sudo bash network/setup_ap.sh        # 고정 IP + 서비스 enable
sudo systemctl restart mosquitto
sudo reboot
```

적용 후: SSID `science-lab-A`, Pi 고정 IP `192.168.50.1`, MQTT가 LAN(0.0.0.0:1883)에서
익명 허용으로 ESP 접속을 받습니다. mDNS(`science-lab.local`)는 avahi-daemon이 제공.
