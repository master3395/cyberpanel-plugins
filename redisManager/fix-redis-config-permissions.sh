#!/bin/bash
# Fix permissions on Redis config so the panel can read it.
# Run as root with FULL path to this script, e.g.:
#   sudo bash /home/cyberpanel-plugins/redisManager/fix-redis-config-permissions.sh
#   sudo bash /home/cyberpanel-plugins/redisManager/fix-redis-config-permissions.sh /etc/redis/redis.conf
# If path is omitted, uses /etc/redis/redis.conf

set -e
CONF="${1:-/etc/redis/redis.conf}"
if [ ! -f "$CONF" ]; then
    echo "File not found: $CONF"
    exit 1
fi
# Resolve symlinks
REAL="$(readlink -f "$CONF" 2>/dev/null || realpath "$CONF" 2>/dev/null || echo "$CONF")"
case "$REAL" in
    /etc/*|/usr/local/*|/opt/*|/var/*) ;;
    *)
        echo "Path not in allowed directory: $REAL"
        exit 1
        ;;
esac
chmod 644 "$REAL"
PARENT="$(dirname "$REAL")"
[ -d "$PARENT" ] && chmod 755 "$PARENT" 2>/dev/null || true
echo "Permissions set: $REAL (644). Reload Redis Manager in the panel."
