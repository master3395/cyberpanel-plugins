#!/bin/bash
set -euo pipefail
SRC="$(cd "$(dirname "$0")" && pwd)"
DEST="/usr/local/CyberCP/port_manager"
echo "[Port Manager] Installing to $DEST ..."
rm -rf "$DEST"
mkdir -p "$DEST"
cp -a "$SRC/port_manager/." "$DEST/"
cp "$SRC/meta.xml" "$DEST/meta.xml"
SETTINGS="/usr/local/CyberCP/CyberCP/settings.py"
if ! grep -q "'port_manager'" "$SETTINGS" 2>/dev/null; then
  echo "[Port Manager] Note: settings.py auto-sync should add port_manager on lscpd restart."
fi
cd /usr/local/CyberCP
python3 manage.py makemigrations port_manager 2>/dev/null || true
python3 manage.py migrate port_manager --noinput 2>/dev/null || true
echo "[Port Manager] Restarting lscpd ..."
systemctl restart lscpd
sleep 2
PORT=$(grep -oE 'address \*:[0-9]+' /usr/local/lscp/conf/bind.conf 2>/dev/null | head -1 | grep -oE '[0-9]+' || echo "8090")
echo "[Port Manager] Test: curl -k -sI https://127.0.0.1:${PORT}/plugins/port_manager/"
curl -k -sI "https://127.0.0.1:${PORT}/plugins/port_manager/" | head -5 || true
echo "[Port Manager] Done."
