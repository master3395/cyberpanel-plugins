#!/bin/bash
# Verify Redis Manager. Run on the CyberPanel server for full checks.
# Usage: bash verify-on-server.sh [base_url]
#   base_url default: https://127.0.0.1:2087 (run on server)
#   base_url e.g. https://207.180.193.210:2087 = test that host (steps 3-4 then check local paths)

set -e
BASE="${1:-https://127.0.0.1:2087}"
URL="$BASE/plugins/redisManager/api/detect-config/"
CYBERCP="${CYBERCP:-/usr/local/CyberCP}"
REPO="${REPO_DIR:-/home/cyberpanel-plugins}"
# If BASE is not localhost/127.0.0.1, we may be running remotely; skip file checks or run them for local install
REMOTE=0
case "$BASE" in *207.180.*|*://[^/]*[0-9][0-9]*\.[0-9]*\.[0-9]*.*) REMOTE=1;; esac

echo "=== Redis Manager verification ==="
echo ""

echo "[1] API endpoint (unauthenticated may get 302):"
HTTP=$(curl -sk -o /tmp/rm_verify_body -w "%{http_code}" "$URL" 2>/dev/null || echo "000")
echo "    GET $URL -> HTTP $HTTP"
if [ "$HTTP" = "200" ]; then
    echo "    Body: $(head -c 200 /tmp/rm_verify_body 2>/dev/null)"
    echo "    OK: API returned 200."
elif [ "$HTTP" = "302" ]; then
    echo "    OK: 302 = redirect to login (route exists, auth required)."
elif [ "$HTTP" = "404" ]; then
    echo "    FAIL: 404 = route missing. Run fix-redis-manager-on-server.sh on the server."
    exit 1
else
    echo "    Got HTTP $HTTP (check URL and lscpd)."
fi
rm -f /tmp/rm_verify_body
echo ""

echo "[2] Python detection (from plugin utils):"
if [ -d "$REPO/redisManager" ]; then
    (cd "$REPO" && python3 -c "
import sys
sys.path.insert(0, '.')
from redisManager import utils
path = utils.detect_redis_config_path()
print('    detect_redis_config_path():', repr(path))
print('    REDIS_CONF_PATHS:', len(utils.REDIS_CONF_PATHS), 'paths')
" 2>/dev/null) || echo "    (run from repo: cd $REPO && python3 redisManager/run_detect_test.py)"
else
    if [ -d "$CYBERCP/redisManager" ]; then
        (cd "$CYBERCP" && python3 -c "
import sys
sys.path.insert(0, '.')
from redisManager import utils
path = utils.detect_redis_config_path()
print('    detect_redis_config_path():', repr(path))
" 2>/dev/null) || echo "    (install path: $CYBERCP/redisManager)"
    else
        echo "    Skipped (no repo or install path)."
    fi
fi
echo ""

if [ "$REMOTE" = "1" ] && [ ! -d "$CYBERCP" ]; then
    echo "[3-4] Skipped (remote URL; run this script on the server for urlconf/plugin checks)."
else
    echo "[3] Main urlconf has redisManager route:"
    if [ -f "${CYBERCP}/CyberCP/urls.py" ] && grep -q "plugins/redisManager/" "${CYBERCP}/CyberCP/urls.py" 2>/dev/null; then
        echo "    OK: path('plugins/redisManager/', ...) found."
    else
        echo "    FAIL: redisManager route not found. Run fix-redis-manager-on-server.sh."
        exit 1
    fi
    echo ""

    echo "[4] Plugin urls.py has api/detect-config/:"
    if [ -f "$CYBERCP/redisManager/urls.py" ] && grep -q "api/detect-config/" "$CYBERCP/redisManager/urls.py" 2>/dev/null; then
        echo "    OK: api/detect-config/ found."
    else
        echo "    FAIL: api/detect-config/ not in plugin urls. Run fix-redis-manager-on-server.sh /path/to/repo."
        exit 1
    fi
fi
echo ""

echo "=== Verification done ==="
