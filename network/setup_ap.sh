#!/bin/bash
# Science AI Lab — AP 고정IP + 서비스 활성화 (콘솔에서 sudo 실행)
set -e
# wlan0 고정 IP (dhcpcd 기준)
if ! grep -q "science-lab AP" /etc/dhcpcd.conf 2>/dev/null; then
cat >> /etc/dhcpcd.conf <<'CONF'

# science-lab AP
interface wlan0
static ip_address=192.168.50.1/24
nohook wpa_supplicant
CONF
fi
systemctl unmask hostapd || true
systemctl enable hostapd dnsmasq avahi-daemon
echo "==> 적용됨. 재부팅하면 science-lab-A AP가 뜹니다."
