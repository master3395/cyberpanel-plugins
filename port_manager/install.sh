#!/bin/bash
# CyberPanel Port Manager - Installation Script
# Flat plugin layout: Django app files live in this directory (no nested port_manager/).

set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

if [ "${EUID:-$(id -u)}" -ne 0 ]; then
  echo -e "${RED}Error: run as root${NC}"
  exit 1
fi

if [ ! -d /usr/local/CyberCP ]; then
  echo -e "${RED}Error: CyberPanel not found at /usr/local/CyberCP${NC}"
  exit 1
fi

SRC="$(cd "$(dirname "$0")" && pwd)"
DEST="/usr/local/CyberCP/port_manager"
MARKER="/home/cyberpanel/plugins/port_manager"

echo "[Port Manager] Installing from $SRC to $DEST ..."

rm -rf "$DEST"
mkdir -p "$DEST" "$MARKER"

if command -v rsync >/dev/null 2>&1; then
  rsync -a \
    --exclude 'install.sh' \
    --exclude 'uninstall.sh' \
    --exclude 'to-do/' \
    --exclude 'test/' \
    --exclude 'mcp/' \
    --exclude 'systemd/' \
    --exclude 'README.md' \
    --exclude 'CHANGELOG.md' \
    "$SRC/" "$DEST/"
  rsync -a \
    --exclude 'install.sh' \
    --exclude 'uninstall.sh' \
    --exclude 'to-do/' \
    --exclude 'test/' \
    --exclude 'mcp/' \
    --exclude 'systemd/' \
    --exclude 'README.md' \
    --exclude 'CHANGELOG.md' \
    "$SRC/" "$MARKER/"
else
  shopt -s dotglob
  for item in "$SRC"/*; do
    base=$(basename "$item")
    case "$base" in
      install.sh|uninstall.sh|to-do|test|mcp|systemd|README.md|CHANGELOG.md)
        continue
        ;;
    esac
    cp -a "$item" "$DEST/"
    cp -a "$item" "$MARKER/"
  done
fi

chown -R root:root "$DEST" 2>/dev/null || true
chmod -R u=rwX,go=rX "$DEST" 2>/dev/null || true

cd /usr/local/CyberCP
python3 manage.py makemigrations port_manager 2>/dev/null || true
python3 manage.py migrate port_manager --noinput 2>/dev/null || true

echo "[Port Manager] Restarting lscpd ..."
systemctl restart lscpd
sleep 2

PORT=$(grep -oE '[0-9]+' /usr/local/lscp/conf/bind.conf 2>/dev/null | head -1)
PORT=${PORT:-8090}
echo "[Port Manager] Test: curl -k -sI https://127.0.0.1:${PORT}/plugins/port_manager/"
curl -k -sI "https://127.0.0.1:${PORT}/plugins/port_manager/" | head -5 || true
echo -e "${GREEN}[Port Manager] Done.${NC}"
