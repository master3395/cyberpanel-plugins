#!/bin/bash
# Fix SnappyMail data folder permissions so the web app can access it.
# Run as root: sudo bash fix_snappymail_permissions.sh
# Use when you see: "SnappyMail can not access the data folder /usr/local/lscp/cyberpanel/snappymail/data/"

set -e

SNAPPYMAIL_DATA='/usr/local/lscp/cyberpanel/snappymail/data'
PUBLIC_SNAPPY='/usr/local/CyberCP/public/snappymail'

echo "SnappyMail data permission fix..."

# Create data directory and subdirs if missing
if [ ! -d "$SNAPPYMAIL_DATA" ]; then
    echo "Creating SnappyMail data directory: $SNAPPYMAIL_DATA"
    mkdir -p "$SNAPPYMAIL_DATA/_data_/_default_/configs/"
    mkdir -p "$SNAPPYMAIL_DATA/_data_/_default_/domains/"
    mkdir -p "$SNAPPYMAIL_DATA/_data_/_default_/storage/"
    mkdir -p "$SNAPPYMAIL_DATA/_data_/_default_/temp/"
    mkdir -p "$SNAPPYMAIL_DATA/_data_/_default_/cache/"
fi

# Ensure parent path exists so we can chown the whole tree
mkdir -p "$SNAPPYMAIL_DATA/_data_/_default_/configs/"
mkdir -p "$SNAPPYMAIL_DATA/_data_/_default_/domains/"
mkdir -p "$SNAPPYMAIL_DATA/_data_/_default_/storage/"
mkdir -p "$SNAPPYMAIL_DATA/_data_/_default_/temp/"
mkdir -p "$SNAPPYMAIL_DATA/_data_/_default_/cache/"

# Set ownership so lscpd (panel) and nobody (web) can access
if id -u lscpd >/dev/null 2>&1; then
    chown -R lscpd:lscpd /usr/local/lscp/cyberpanel/snappymail/
    echo "Set ownership to lscpd:lscpd for /usr/local/lscp/cyberpanel/snappymail/"
else
    echo "WARNING: lscpd user not found. Trying nobody:nobody."
    chown -R nobody:nobody /usr/local/lscp/cyberpanel/snappymail/ 2>/dev/null || true
fi

# Group-writable so PHP (often running as nobody) can write when in lscpd group
chmod -R 775 "$SNAPPYMAIL_DATA"
# application.ini must be writable by PHP when plugin runs from panel (often nobody); 666 so any process can write
CONFIG_INI="$SNAPPYMAIL_DATA/_data_/_default_/configs/application.ini"
[ -f "$CONFIG_INI" ] && chmod 666 "$CONFIG_INI" && echo "Set application.ini to 666 (writable by PHP)"
echo "Set data directory permissions to 775"

# Add nobody to lscpd group so PHP (nobody) can access lscpd-owned files
if id -u lscpd >/dev/null 2>&1 && id -u nobody >/dev/null 2>&1; then
    usermod -a -G lscpd nobody 2>/dev/null || true
    echo "Added nobody to lscpd group (if not already)."
fi

# Fix public snappymail data symlink/dir if it exists
if [ -d "$PUBLIC_SNAPPY/data" ] || [ -e "$PUBLIC_SNAPPY/data" ]; then
    chown -R lscpd:lscpd "$PUBLIC_SNAPPY/data" 2>/dev/null || true
    echo "Fixed ownership for $PUBLIC_SNAPPY/data"
fi

echo "Done. Reload https://your-panel:2087/snappymail/ or /plugins/snappymailAdmin/"
