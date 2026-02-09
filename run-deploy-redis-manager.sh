#!/bin/bash
# One-shot: ensure redisManager is deployed and installed on this CyberPanel server.
# Run on the server: curl -sSL <url> | bash   OR   ./run-deploy-redis-manager.sh

set -e
REPO_DIR="${REPO_DIR:-/home/cyberpanel-plugins}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd)"
if [ -n "$SCRIPT_DIR" ] && [ -d "$SCRIPT_DIR" ]; then
    REPO_DIR="$SCRIPT_DIR"
fi
cd "$REPO_DIR" || { echo "Missing $REPO_DIR"; exit 1; }
chmod +x deploy-redis-manager.sh 2>/dev/null || true
exec ./deploy-redis-manager.sh
