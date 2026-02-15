#!/bin/bash
# Add snappymailAdmin to CyberPanel INSTALLED_APPS and restart panel.
# Run as root on the server: bash install.sh  or  ./install.sh

set -e
SETTINGS='/usr/local/CyberCP/CyberCP/settings.py'
APP_NAME='snappymailAdmin'

if [ ! -f "$SETTINGS" ]; then
    echo "Error: $SETTINGS not found. Is CyberPanel installed?"
    exit 1
fi

if grep -q "'${APP_NAME}'" "$SETTINGS" 2>/dev/null; then
    echo "${APP_NAME} is already in INSTALLED_APPS."
else
    python3 - "$SETTINGS" "$APP_NAME" << 'PY'
import sys
path = sys.argv[1]
app = sys.argv[2]
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()
out = []
added = False
in_apps = False
for line in lines:
    if "INSTALLED_APPS" in line and "=" in line:
        in_apps = True
    if in_apps and not added:
        # Insert after emailPremium, pluginHolder, or before closing ]
        if "'emailPremium'," in line or '"emailPremium",' in line:
            out.append(line)
            out.append("    '%s',\n" % app)
            added = True
            continue
        if "'pluginHolder'," in line or '"pluginHolder",' in line:
            out.append(line)
            out.append("    '%s',\n" % app)
            added = True
            continue
        if line.strip().startswith(']'):
            out.append("    '%s',\n" % app)
            added = True
    out.append(line)
if not added:
    print("Warning: could not find insertion point in INSTALLED_APPS", file=sys.stderr)
    sys.exit(1)
with open(path, 'w', encoding='utf-8') as f:
    f.writelines(out)
print("Added '%s' to INSTALLED_APPS." % app)
PY
    echo "Updated $SETTINGS"
fi

# Fix SnappyMail data folder permissions so the web app can access it (avoids "Permission denied" on data folder)
if [ -d /usr/local/CyberCP/public/snappymail ]; then
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
    if [ -x "$SCRIPT_DIR/fix_snappymail_permissions.sh" ]; then
        "$SCRIPT_DIR/fix_snappymail_permissions.sh"
    elif [ -f "$SCRIPT_DIR/fix_snappymail_permissions.sh" ]; then
        bash "$SCRIPT_DIR/fix_snappymail_permissions.sh"
    fi
fi

# Restart panel so URL config is reloaded
if command -v systemctl >/dev/null 2>&1 && systemctl is-active --quiet lscpd 2>/dev/null; then
    systemctl restart lscpd
    echo "Restarted lscpd."
elif [ -x /usr/local/lsws/bin/lswsctrl ]; then
    /usr/local/lsws/bin/lswsctrl restart
    echo "Restarted LiteSpeed."
else
    echo "Please restart your panel (e.g. systemctl restart lscpd) for changes to take effect."
fi
echo "Done. Open https://YOUR-PANEL:2087/plugins/snappymailAdmin/"
