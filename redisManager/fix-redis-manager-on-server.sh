#!/bin/bash
# Fix Redis Manager 404 and old "Paths tried" on the CyberPanel server.
# Run on the server as root: bash fix-redis-manager-on-server.sh
# Optional: bash fix-redis-manager-on-server.sh /home/cyberpanel-plugins
#   to also copy updated utils.py, views.py, urls.py, index.html from that path.

set -e
CYBERCP="${CYBERCP:-/usr/local/CyberCP}"
MAIN_URLS="$CYBERCP/CyberCP/urls.py"
PLUGIN_DIR="$CYBERCP/redisManager"
PLUGIN_URLS="$PLUGIN_DIR/urls.py"
SOURCE_DIR="${1:-}"

echo "[1/5] Patching main URLconf ($MAIN_URLS)..."
if [ ! -f "$MAIN_URLS" ]; then
    echo "  ERROR: $MAIN_URLS not found. Is CyberPanel installed?"
    exit 1
fi
if ! grep -q "plugins/redisManager/" "$MAIN_URLS"; then
    cp -a "$MAIN_URLS" "${MAIN_URLS}.bak.$(date +%Y%m%d%H%M%S)"
    # Insert redisManager before generic plugins/ line (match single- or double-quoted path)
    if grep -q "path('plugins/', include('pluginHolder.urls'))" "$MAIN_URLS"; then
        sed -i "/path('plugins\/', include('pluginHolder.urls'))/i \    path('plugins/redisManager/', include('redisManager.urls'))," "$MAIN_URLS"
    elif grep -q 'path("plugins/', "$MAIN_URLS"; then
        sed -i '/path("plugins\/", include.*pluginHolder.urls.*)/i \    path("plugins/redisManager/", include("redisManager.urls")),' "$MAIN_URLS"
    else
        echo "  WARN: Could not find plugins/ line in $MAIN_URLS; add path('plugins/redisManager/', include('redisManager.urls')), before path('plugins/', ...) manually."
    fi
    echo "  Added plugins/redisManager/ route."
else
    echo "  redisManager route already present."
fi

echo "[2/5] Plugin directory and urls.py..."
if [ ! -d "$PLUGIN_DIR" ] || [ ! -f "$PLUGIN_URLS" ]; then
    if [ -n "$SOURCE_DIR" ] && [ -d "$SOURCE_DIR" ]; then
        SRC="$SOURCE_DIR/redisManager"
        if [ -d "$SRC" ] && [ -f "$SRC/urls.py" ]; then
            echo "  Plugin not installed; installing from $SRC into $PLUGIN_DIR..."
            mkdir -p "$PLUGIN_DIR"
            cp -a "$SRC"/*.py "$SRC"/meta.xml "$PLUGIN_DIR" 2>/dev/null || true
            [ -f "$SRC/urls.py" ] && cp -a "$SRC/urls.py" "$PLUGIN_DIR/"
            [ -f "$SRC/views.py" ] && cp -a "$SRC/views.py" "$PLUGIN_DIR/"
            [ -f "$SRC/utils.py" ] && cp -a "$SRC/utils.py" "$PLUGIN_DIR/"
            [ -f "$SRC/apps.py" ] && cp -a "$SRC/apps.py" "$PLUGIN_DIR/"
            [ -f "$SRC/__init__.py" ] && cp -a "$SRC/__init__.py" "$PLUGIN_DIR/"
            mkdir -p "$PLUGIN_DIR/templates/redisManager"
            [ -f "$SRC/templates/redisManager/index.html" ] && cp -a "$SRC/templates/redisManager/index.html" "$PLUGIN_DIR/templates/redisManager/"
            echo "  Installed redisManager from repo (urls, views, utils, templates)."
        else
            echo "  WARN: $PLUGIN_URLS not found and no SOURCE_DIR repo. Run: $0 /home/cyberpanel-plugins"
            exit 1
        fi
    else
        echo "  WARN: $PLUGIN_URLS not found. Run with repo path: $0 /home/cyberpanel-plugins"
        exit 1
    fi
else
    if ! grep -q "api/detect-config/" "$PLUGIN_URLS"; then
        cp -a "$PLUGIN_URLS" "${PLUGIN_URLS}.bak.$(date +%Y%m%d%H%M%S)"
        sed -i "/path('api\/save-config-path\/'/a \    path('api/detect-config/', views.api_detect_config, name='api_detect_config')," "$PLUGIN_URLS"
        echo "  Added api/detect-config/ route."
    else
        echo "  api/detect-config/ already present."
    fi
fi

echo "[3/5] Copying updated plugin files (if SOURCE_DIR provided and plugin already exists)..."
if [ -n "$SOURCE_DIR" ] && [ -d "$SOURCE_DIR" ] && [ -d "$PLUGIN_DIR" ]; then
    SRC="$SOURCE_DIR/redisManager"
    if [ -f "$SRC/utils.py" ]; then
        cp -a "$SRC/utils.py" "$PLUGIN_DIR/utils.py"
        echo "  Copied utils.py (expanded detection + 7 paths)."
    fi
    if [ -f "$SRC/views.py" ]; then
        cp -a "$SRC/views.py" "$PLUGIN_DIR/views.py"
        echo "  Copied views.py."
    fi
    if [ -f "$SRC/urls.py" ]; then
        cp -a "$SRC/urls.py" "$PLUGIN_DIR/urls.py"
        echo "  Copied urls.py."
    fi
    if [ -f "$SRC/templates/redisManager/index.html" ]; then
        mkdir -p "$PLUGIN_DIR/templates/redisManager"
        cp -a "$SRC/templates/redisManager/index.html" "$PLUGIN_DIR/templates/redisManager/index.html"
        echo "  Copied templates/redisManager/index.html."
    fi
elif [ -z "$SOURCE_DIR" ] || [ ! -d "$SOURCE_DIR" ]; then
    if [ -d "$PLUGIN_DIR" ]; then
        echo "  Skipped (no SOURCE_DIR; run with path to repo to update files, e.g. $0 /home/cyberpanel-plugins)."
    fi
fi

echo "[4/5] Adding redisManager to INSTALLED_APPS (required for template loading)..."
SETTINGS="$CYBERCP/CyberCP/settings.py"
if [ -f "$SETTINGS" ]; then
    if ! grep -q "'redisManager'" "$SETTINGS" && ! grep -q '"redisManager"' "$SETTINGS"; then
        cp -a "$SETTINGS" "${SETTINGS}.bak.$(date +%Y%m%d%H%M%S)"
        if grep -q "'emailPremium'" "$SETTINGS"; then
            sed -i "/'emailPremium',/a \    'redisManager'," "$SETTINGS"
            echo "  Added 'redisManager' to INSTALLED_APPS (after emailPremium)."
        else
            echo "  WARN: Could not find 'emailPremium' in settings.py. Add 'redisManager' to INSTALLED_APPS manually and restart lscpd."
        fi
    else
        echo "  redisManager already in INSTALLED_APPS."
    fi
else
    echo "  WARN: $SETTINGS not found."
fi

echo "[5/5] Restarting lscpd..."
systemctl restart lscpd 2>/dev/null || { echo "  WARN: could not restart lscpd"; }

echo "Done. Open Redis Manager and click Auto-detect; api/detect-config/ should return 200."
