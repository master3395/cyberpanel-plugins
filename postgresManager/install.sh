#!/bin/bash
set -euo pipefail

APP_NAME="postgresManager"
SRC="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
DEST="/usr/local/CyberCP/${APP_NAME}"
SETTINGS="/usr/local/CyberCP/CyberCP/settings.py"
PLUGIN_URLS="/usr/local/CyberCP/pluginHolder/urls.py"
ADMINER_DIR="/usr/local/CyberCP/public/postgres-adminer"
STATE_DIR="/usr/local/CyberCP/pluginState/postgresManager"
ADMIN_ROLE="cyberpanel_pgadmin"
ADMIN_DB="cyberpanel_postgres"
PASSWORD_FILE="${STATE_DIR}/cyberpanel_pgadmin_password"

log() { printf '[PostgreSQL Manager] %s\n' "$*"; }
fail() { printf '[PostgreSQL Manager] Error: %s\n' "$*" >&2; exit 1; }

require_root() {
    if [ "$(id -u)" != "0" ]; then
        fail "Run this installer as root."
    fi
}

detect_pkg_manager() {
    if command -v dnf >/dev/null 2>&1; then echo dnf; return; fi
    if command -v yum >/dev/null 2>&1; then echo yum; return; fi
    if command -v apt-get >/dev/null 2>&1; then echo apt; return; fi
    fail "No supported package manager found. Supported: dnf, yum, apt-get."
}

install_packages() {
    local pm="$1"
    log "Installing PostgreSQL packages..."
    case "$pm" in
        dnf|yum)
            "$pm" install -y postgresql-server postgresql-contrib
            ;;
        apt)
            apt-get update
            DEBIAN_FRONTEND=noninteractive apt-get install -y postgresql postgresql-contrib
            ;;
    esac
}

install_php_pgsql() {
    local pm="$1"
    log "Installing PHP PostgreSQL extension for CyberPanel PHP..."
    case "$pm" in
        dnf|yum)
            local installed_any=0
            local php_bins=()
            while IFS= read -r phpbin; do
                [ -n "$phpbin" ] && php_bins+=("$phpbin")
            done < <(awk '
                /extprocessor cyberpanelphp/,/^}/ {
                    if ($1 == "path" && $2 ~ /^\/usr\/local\/lsws\/lsphp[0-9]+\/bin\/lsphp$/) print $2
                }
                /extprocessor lsphp/,/^}/ {
                    if ($1 == "path" && $2 ~ /^\/usr\/local\/lsws\/lsphp[0-9]+\/bin\/lsphp$/) print $2
                }
            ' /usr/local/lsws/conf/httpd_config.conf /usr/local/lsws/conf/vhosts/*/vhost.conf 2>/dev/null | sort -u)
            if [ "${#php_bins[@]}" = "0" ]; then
                php_bins=(/usr/local/lsws/lsphp*/bin/lsphp)
            fi
            for phpbin in "${php_bins[@]}"; do
                [ -x "$phpbin" ] || continue
                local version_dir
                version_dir="$(basename "$(dirname "$(dirname "$phpbin")")")"
                "$pm" install -y "${version_dir}-pgsql" && installed_any=1 || true
            done
            if [ "$installed_any" = "0" ]; then
                log "No /usr/local/lsws/lsphp*/bin/lsphp installation found or pgsql package unavailable. Adminer may need php-pgsql installed manually."
            fi
            ;;
        apt)
            DEBIAN_FRONTEND=noninteractive apt-get install -y php-pgsql || true
            ;;
    esac
}

init_postgresql() {
    log "Initializing and enabling PostgreSQL..."
    if command -v postgresql-setup >/dev/null 2>&1; then
        if [ ! -f /var/lib/pgsql/data/PG_VERSION ]; then
            postgresql-setup --initdb
        fi
        systemctl enable --now postgresql
    else
        systemctl enable --now postgresql || systemctl enable --now postgresql@*-main || true
    fi
}

postgres_service_name() {
    for svc in postgresql postgresql-16 postgresql-15 postgresql-14 postgresql-13; do
        if systemctl status "$svc" >/dev/null 2>&1; then
            echo "$svc"
            return
        fi
    done
    systemctl list-units --type=service --all --no-legend 'postgresql*' 2>/dev/null | awk '{print $1; exit}'
}

ensure_local_bind() {
    local conf=""
    for candidate in /var/lib/pgsql/data/postgresql.conf /etc/postgresql/*/main/postgresql.conf; do
        if [ -f "$candidate" ]; then conf="$candidate"; break; fi
    done
    [ -n "$conf" ] || return 0
    if grep -Eq "^[#[:space:]]*listen_addresses[[:space:]]*=" "$conf"; then
        sed -i "s/^[#[:space:]]*listen_addresses[[:space:]]*=.*/listen_addresses = 'localhost'/" "$conf"
    else
        printf "\nlisten_addresses = 'localhost'\n" >> "$conf"
    fi
}

ensure_local_password_auth() {
    local hba=""
    for candidate in /var/lib/pgsql/data/pg_hba.conf /etc/postgresql/*/main/pg_hba.conf; do
        if [ -f "$candidate" ]; then hba="$candidate"; break; fi
    done
    [ -n "$hba" ] || return 0
    if grep -q "cyberpanel-postgres-manager" "$hba"; then
        return 0
    fi
    cp -a "$hba" "${hba}.bak-postgresManager-$(date +%Y%m%d%H%M%S)"
    python3 - "$hba" "$ADMIN_ROLE" "$ADMIN_DB" <<'PY'
import sys
path, role, db = sys.argv[1], sys.argv[2], sys.argv[3]
with open(path, 'r', encoding='utf-8') as f:
    data = f.read()
block = """# cyberpanel-postgres-manager begin
host    {db}             {role}             127.0.0.1/32            md5
host    {db}             {role}             ::1/128                 md5
host    all              {role}             127.0.0.1/32            md5
host    all              {role}             ::1/128                 md5
# cyberpanel-postgres-manager end

""".format(db=db, role=role)
marker = "# TYPE  DATABASE"
idx = data.find(marker)
if idx >= 0:
    line_end = data.find("\n", idx)
    data = data[:line_end + 1] + block + data[line_end + 1:]
else:
    data += "\n" + block
with open(path, 'w', encoding='utf-8') as f:
    f.write(data)
PY
}

ensure_admin_role() {
    log "Creating dedicated PostgreSQL admin role..."
    install -d -m 700 "$STATE_DIR"
    if [ ! -f "$PASSWORD_FILE" ]; then
        openssl rand -base64 32 | tr -d '\n' > "$PASSWORD_FILE"
        printf '\n' >> "$PASSWORD_FILE"
        chmod 600 "$PASSWORD_FILE"
    fi
    local pass
    pass="$(cat "$PASSWORD_FILE")"
    local escaped
    escaped="${pass//\'/\'\'}"
    runuser -u postgres -- psql -v ON_ERROR_STOP=1 -c "DO \$\$ BEGIN IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '${ADMIN_ROLE}') THEN CREATE ROLE ${ADMIN_ROLE} WITH LOGIN CREATEDB CREATEROLE PASSWORD '${escaped}'; ELSE ALTER ROLE ${ADMIN_ROLE} WITH LOGIN CREATEDB CREATEROLE PASSWORD '${escaped}'; END IF; END \$\$;"
    if ! runuser -u postgres -- psql -Atqc "SELECT 1 FROM pg_database WHERE datname='${ADMIN_DB}'" | grep -q 1; then
        runuser -u postgres -- createdb -O "$ADMIN_ROLE" "$ADMIN_DB"
    fi
}

install_adminer() {
    log "Installing Adminer PostgreSQL console..."
    install -d -m 755 "$ADMINER_DIR"
    local adminer_target="${ADMINER_DIR}/adminer.php"
    if command -v curl >/dev/null 2>&1; then
        curl -fsSL "https://www.adminer.org/latest.php" -o "$adminer_target"
    elif command -v wget >/dev/null 2>&1; then
        wget -qO "$adminer_target" "https://www.adminer.org/latest.php"
    else
        fail "curl or wget is required to download Adminer."
    fi
    cat > "${ADMINER_DIR}/index.php" <<'PHP'
<?php
// CyberPanel PostgreSQL Manager ships stock Adminer for maximum compatibility.
// Select "PostgreSQL" in System and use credentials shown in /plugins/postgresManager/.
include __DIR__ . "/adminer.php";
PHP
    chown -R lscpd:lscpd "$ADMINER_DIR" 2>/dev/null || true
    chmod 644 "${ADMINER_DIR}/adminer.php" "${ADMINER_DIR}/index.php"
}

copy_plugin() {
    log "Installing Django plugin files..."
    rm -rf "$DEST"
    mkdir -p "$DEST"
    cp -a "$SRC/." "$DEST/"
    find "$DEST" -type d -exec chmod 755 {} \;
    find "$DEST" -type f -exec chmod 644 {} \;
    chmod 755 "$DEST/install.sh"
}

patch_installed_apps() {
    [ -f "$SETTINGS" ] || fail "$SETTINGS not found. Is CyberPanel installed?"
    if grep -q "'${APP_NAME}'" "$SETTINGS" 2>/dev/null; then
        log "${APP_NAME} already registered in INSTALLED_APPS."
        return
    fi
    python3 - "$SETTINGS" "$APP_NAME" <<'PY'
import sys
path, app = sys.argv[1], sys.argv[2]
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()
out, added, in_apps = [], False, False
for line in lines:
    if "INSTALLED_APPS" in line and "=" in line:
        in_apps = True
    if in_apps and not added and line.strip().startswith(']'):
        out.append("    '%s',\n" % app)
        added = True
    out.append(line)
if not added:
    raise SystemExit("Could not find INSTALLED_APPS insertion point.")
with open(path, 'w', encoding='utf-8') as f:
    f.writelines(out)
PY
}

patch_plugin_urls_fallback() {
    [ -f "$PLUGIN_URLS" ] || return 0
    if grep -q "${APP_NAME}.urls" "$PLUGIN_URLS" 2>/dev/null; then
        return 0
    fi
    if grep -q "_get_installed_plugin_list" "$PLUGIN_URLS" 2>/dev/null; then
        log "Dynamic plugin router detected. No URL fallback patch needed."
        return 0
    fi
    log "Adding URL fallback to pluginHolder/urls.py..."
    cp -a "$PLUGIN_URLS" "${PLUGIN_URLS}.bak-postgresManager-$(date +%Y%m%d%H%M%S)"
    python3 - "$PLUGIN_URLS" "$APP_NAME" <<'PY'
import sys
path, app = sys.argv[1], sys.argv[2]
with open(path, 'r', encoding='utf-8') as f:
    data = f.read()
data = data.replace('from django.urls import path\n', 'from django.urls import path, include\n')
needle = 'urlpatterns = [\n'
route = "    path('%s/', include('%s.urls')),\n" % (app, app)
if route not in data:
    data = data.replace(needle, needle + route, 1)
with open(path, 'w', encoding='utf-8') as f:
    f.write(data)
PY
}

patch_panel_vhosts() {
    log "Adding OpenLiteSpeed context for /postgres-adminer/..."
    local changed=0
    for conf in /usr/local/lsws/conf/vhosts/*/vhost.conf; do
        [ -f "$conf" ] || continue
        grep -q "context /phpmyadmin/" "$conf" || grep -q "context /snappymail/" "$conf" || continue
        if grep -q "context /postgres-adminer/" "$conf"; then
            continue
        fi
        cp -a "$conf" "${conf}.bak-postgresManager-$(date +%Y%m%d%H%M%S)"
        python3 - "$conf" <<'PY'
import sys
path = sys.argv[1]
with open(path, 'r', encoding='utf-8') as f:
    data = f.read()
block = """context /postgres-adminer/ {
  location                /usr/local/CyberCP/public/postgres-adminer/
  allowBrowse             1
  indexFiles              index.php
  addDefaultCharset       off
  scripthandler  {
    add                     lsapi:cyberpanelphp php
  }
}

"""
marker = "context /static/ {"
if marker in data:
    data = data.replace(marker, block + marker, 1)
else:
    data += "\n" + block
with open(path, 'w', encoding='utf-8') as f:
    f.write(data)
PY
        changed=1
    done
    if [ "$changed" = "0" ]; then
        log "No panel vhost with phpMyAdmin/SnappyMail context found. Add /postgres-adminer/ context manually if needed."
    fi
}

restart_services() {
    local svc
    svc="$(postgres_service_name || true)"
    if [ -n "$svc" ]; then
        systemctl restart "$svc" || true
    fi
    if systemctl is-active --quiet lscpd 2>/dev/null; then
        systemctl restart lscpd
    fi
    if [ -x /usr/local/lsws/bin/lswsctrl ]; then
        /usr/local/lsws/bin/lswsctrl restart || true
    elif ! systemctl is-active --quiet lscpd 2>/dev/null; then
        log "Restart CyberPanel/OpenLiteSpeed manually."
    fi
}

main() {
    require_root
    local pm
    pm="$(detect_pkg_manager)"
    install_packages "$pm"
    install_php_pgsql "$pm"
    init_postgresql
    ensure_local_bind
    ensure_local_password_auth
    ensure_admin_role
    install_adminer
    copy_plugin
    patch_installed_apps
    patch_plugin_urls_fallback
    patch_panel_vhosts
    restart_services
    log "Done. Open https://YOUR-PANEL/plugins/postgresManager/"
    log "Adminer URL: https://YOUR-PANEL/postgres-adminer/"
    log "PostgreSQL user: ${ADMIN_ROLE}"
    log "Password file: ${PASSWORD_FILE}"
}

main "$@"
