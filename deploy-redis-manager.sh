#!/bin/bash
# Deploy and install Redis Manager plugin so it appears as installed and active.
# Run on the CyberPanel server from the cyberpanel-plugins repo root, or set REPO_DIR.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="${REPO_DIR:-$SCRIPT_DIR}"
CYBERCP_DIR="${CYBERCP_DIR:-/usr/local/CyberCP}"
PLUGIN_HOLDER_DIR="$CYBERCP_DIR/pluginHolder"
PLUGIN_STATE_DIR="${PLUGIN_STATE_DIR:-/home/cyberpanel/plugin_states}"
PYTHON_BIN="${PYTHON_BIN:-$CYBERCP_DIR/bin/python}"
PLUGIN_NAME="redisManager"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

if [ ! -d "$REPO_DIR/$PLUGIN_NAME" ] || [ ! -f "$REPO_DIR/$PLUGIN_NAME/meta.xml" ]; then
    log_error "Plugin source not found: $REPO_DIR/$PLUGIN_NAME (with meta.xml). Run from repo root or set REPO_DIR."
    exit 1
fi

ZIP_FILE="/tmp/${PLUGIN_NAME}.zip"
log_info "Creating ZIP for $PLUGIN_NAME..."
cd "$REPO_DIR"
zip -r "$ZIP_FILE" "$PLUGIN_NAME" -x "*.pyc" -x "__pycache__/*" -x "*.git/*" -x "*.gitignore" > /dev/null 2>&1 || {
    log_error "Failed to create ZIP"
    exit 1
}

if [ -d "$CYBERCP_DIR/$PLUGIN_NAME" ]; then
    log_warn "$PLUGIN_NAME already installed; replacing..."
    rm -rf "$CYBERCP_DIR/$PLUGIN_NAME"
fi

log_info "Installing $PLUGIN_NAME..."
cp "$ZIP_FILE" "$PLUGIN_HOLDER_DIR/"
cd "$PLUGIN_HOLDER_DIR"
"$PYTHON_BIN" "$CYBERCP_DIR/pluginInstaller/pluginInstaller.py" installPlugin --pluginName "$PLUGIN_NAME" 2>&1 || {
    log_error "pluginInstaller failed; check $CYBERCP_DIR and Python path"
    rm -f "$ZIP_FILE"
    exit 1
}
rm -f "$ZIP_FILE"

mkdir -p "$PLUGIN_STATE_DIR"
echo -n "enabled" > "$PLUGIN_STATE_DIR/${PLUGIN_NAME}.state"
chmod 644 "$PLUGIN_STATE_DIR/${PLUGIN_NAME}.state"
log_info "Plugin enabled: $PLUGIN_STATE_DIR/${PLUGIN_NAME}.state"

if command -v systemctl >/dev/null 2>&1; then
    log_info "Restarting CyberPanel (lscpd)..."
    systemctl restart lscpd 2>/dev/null || true
fi

log_info "Redis Manager deployed and installed. It should appear in Plugins > Installed and be active."
