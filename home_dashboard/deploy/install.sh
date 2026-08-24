#!/usr/bin/env bash
# 라즈베리파이(Raspberry Pi OS)에서 집안 대시보드를 서비스로 설치합니다.
# 사용법: bash deploy/install.sh
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVICE_USER="${SUDO_USER:-$USER}"

echo "==> 파이썬 가상환경 준비 ($APP_DIR/.venv)"
sudo apt-get update -qq
sudo apt-get install -y python3-venv python3-pip
python3 -m venv "$APP_DIR/.venv"
"$APP_DIR/.venv/bin/pip" install --upgrade pip
"$APP_DIR/.venv/bin/pip" install -e "$APP_DIR"

if [ ! -f "$APP_DIR/.env" ]; then
  cp "$APP_DIR/deploy/env.example" "$APP_DIR/.env"
  echo "==> .env 를 만들었습니다. 알림 설정을 채워 넣으세요: $APP_DIR/.env"
fi

echo "==> systemd 서비스 등록"
sed -e "s|/home/pi/home_dashboard|$APP_DIR|g" \
    -e "s|^User=pi$|User=$SERVICE_USER|" \
    "$APP_DIR/deploy/home-dashboard.service" | sudo tee /etc/systemd/system/home-dashboard.service > /dev/null

sudo systemctl daemon-reload
sudo systemctl enable --now home-dashboard

echo
echo "완료! 상태 확인:  sudo systemctl status home-dashboard"
echo "접속 주소:       http://$(hostname -I | awk '{print $1}'):${HOME_PORT:-8000}"
