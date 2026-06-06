#!/bin/bash
set -euo pipefail
systemctl stop cyberpanel-port-manager-mcp 2>/dev/null || true
systemctl disable cyberpanel-port-manager-mcp 2>/dev/null || true
rm -f /etc/systemd/system/cyberpanel-port-manager-mcp.service
systemctl daemon-reload 2>/dev/null || true
rm -rf /usr/local/CyberCP/port_manager
if systemctl is-active --quiet lscpd 2>/dev/null; then
  systemctl reload lscpd || systemctl restart lscpd
fi
echo "[Port Manager] Uninstalled."
