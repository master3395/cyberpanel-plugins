# -*- coding: utf-8 -*-
"""Roundcube Webmail plugin utilities: deploy, enable/disable, status."""
from __future__ import print_function

import json
import os
import secrets
import shutil
import subprocess
import tarfile
import time

from . import ols_utils
from .utils_paths import (
    SETTINGS_FILE,
    DISABLE_MARKER,
    ROUNDCUBE_ROOT,
    ROUNDCUBE_PUBLIC,
    ROUNDCUBE_CONFIG,
    ROUNDCUBE_DB_DIR,
    ROUNDCUBE_SQLITE,
    ROUNDCUBE_VERSION_FILE,
    ROUNDCUBE_FALLBACK_VERSION,
    get_panel_port,
    _log,
)

# Re-export for views/tests
PLUGIN_NAME = 'roundcubeWebmail'


def _default_settings():
    return {
        'enabled': True,
        'installed_version': '',
        'last_deploy_at': '',
        'imap_host': 'localhost:993',
    }


def load_settings():
    settings = _default_settings()
    try:
        if os.path.isfile(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as handle:
                raw = json.load(handle)
            if isinstance(raw, dict):
                settings.update(raw)
    except Exception as exc:
        _log('WARNING: could not read settings: %s' % exc)
    return settings


def save_settings(settings):
    os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
    payload = _default_settings()
    if isinstance(settings, dict):
        payload.update(settings)
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write('\n')
    try:
        os.chmod(SETTINGS_FILE, 0o600)
        subprocess.run(['chown', 'cyberpanel:cyberpanel', SETTINGS_FILE], capture_output=True, timeout=10)
    except Exception:
        pass
    return payload


def is_enabled():
    return bool(load_settings().get('enabled', True))


def set_enabled(enabled):
    settings = load_settings()
    settings['enabled'] = bool(enabled)
    save_settings(settings)
    if enabled:
        enable_serving()
    else:
        disable_serving()
    return settings


def _resolve_roundcube_version():
    version = ROUNDCUBE_FALLBACK_VERSION
    if os.path.isfile(ROUNDCUBE_VERSION_FILE):
        try:
            raw = open(ROUNDCUBE_VERSION_FILE, 'r', encoding='utf-8').read().strip()
            if raw and len(raw) < 20 and all(ch.isdigit() or ch == '.' for ch in raw):
                version = raw
        except Exception:
            pass
    return version


def _build_config_inc_php(des_key):
    sqlite_path = ROUNDCUBE_SQLITE
    return """<?php
$config = array();

$config['db_dsnw'] = 'sqlite:///%s?mode=0646';
$config['imap_host'] = 'localhost:993';
$config['imap_conn_options'] = array(
  'ssl' => array(
    'verify_peer' => false,
    'verify_peer_name' => false,
  ),
);
$config['smtp_host'] = 'localhost:587';
$config['smtp_user'] = '%u';
$config['smtp_pass'] = '%p';
$config['smtp_conn_options'] = array(
  'ssl' => array(
    'verify_peer' => false,
    'verify_peer_name' => false,
  ),
);
$config['product_name'] = 'Roundcube Webmail';
$config['des_key'] = '%s';
$config['plugins'] = array('archive', 'zipdownload');
$config['skin'] = 'elastic';
$config['temp_dir'] = '%s';
$config['log_dir'] = '%s';
$config['enable_installer'] = false;
""" % (
        sqlite_path.replace("'", "\'"),
        des_key.replace("'", "\'"),
        os.path.join(ROUNDCUBE_ROOT, 'temp').replace("'", "\'"),
        os.path.join(ROUNDCUBE_ROOT, 'logs').replace("'", "\'"),
    )


def _write_config(des_key=None):
    if des_key is None:
        if os.path.isfile(ROUNDCUBE_CONFIG):
            try:
                content = open(ROUNDCUBE_CONFIG, 'r', encoding='utf-8', errors='replace').read()
                marker = "$config['des_key'] = '"
                if marker in content:
                    start = content.index(marker) + len(marker)
                    end = content.index("';", start)
                    des_key = content[start:end]
            except Exception:
                des_key = None
        if not des_key:
            des_key = secrets.token_hex(12)
    os.makedirs(os.path.dirname(ROUNDCUBE_CONFIG), exist_ok=True)
    with open(ROUNDCUBE_CONFIG, 'w', encoding='utf-8') as handle:
        handle.write(_build_config_inc_php(des_key))
    os.chmod(ROUNDCUBE_CONFIG, 0o640)
    return des_key


def _ensure_runtime_dirs():
    for path in (ROUNDCUBE_DB_DIR, os.path.join(ROUNDCUBE_ROOT, 'temp'), os.path.join(ROUNDCUBE_ROOT, 'logs')):
        os.makedirs(path, exist_ok=True)
    try:
        subprocess.run(['chown', '-R', 'lscpd:lscpd', ROUNDCUBE_DB_DIR, os.path.join(ROUNDCUBE_ROOT, 'temp'), os.path.join(ROUNDCUBE_ROOT, 'logs')], capture_output=True, timeout=60)
    except Exception:
        pass


def deploy_roundcube(force=False):
    """Download and deploy Roundcube; preserve existing config des_key and sqlite DB when possible."""
    index_public = os.path.join(ROUNDCUBE_PUBLIC, 'index.php')
    existing_des_key = None
    if os.path.isfile(ROUNDCUBE_CONFIG):
        try:
            content = open(ROUNDCUBE_CONFIG, 'r', encoding='utf-8', errors='replace').read()
            marker = "$config['des_key'] = '"
            if marker in content:
                start = content.index(marker) + len(marker)
                end = content.index("';", start)
                existing_des_key = content[start:end]
        except Exception:
            pass

    db_backup = None
    if os.path.isfile(ROUNDCUBE_SQLITE):
        db_backup = ROUNDCUBE_SQLITE + '.cp-backup'
        try:
            shutil.copy2(ROUNDCUBE_SQLITE, db_backup)
        except Exception:
            db_backup = None

    if os.path.isfile(index_public) and not force:
        _write_config(existing_des_key)
        _ensure_runtime_dirs()
        return True, 'Roundcube already deployed'

    version = _resolve_roundcube_version()
    work_dir = '/usr/local/CyberCP/public'
    archive = os.path.join(work_dir, 'roundcubemail-%s-complete.tar.gz' % version)
    url = 'https://github.com/roundcube/roundcubemail/releases/download/%s/roundcubemail-%s-complete.tar.gz' % (version, version)

    if not os.path.isfile(archive):
        result = subprocess.run(['wget', '-q', '-O', archive, url], capture_output=True, text=True, timeout=600)
        if result.returncode != 0:
            return False, 'Download failed: %s' % ((result.stderr or result.stdout or '').strip())

    if os.path.isdir(ROUNDCUBE_ROOT):
        shutil.rmtree(ROUNDCUBE_ROOT)
    os.makedirs(ROUNDCUBE_ROOT, exist_ok=True)

    try:
        import tarfile as _tarfile
        with _tarfile.open(archive, 'r:gz') as tar:
            members = tar.getmembers()
            top_dirs = {m.name.split('/')[0] for m in members if '/' in m.name}
            tar.extractall(path=work_dir)
            extracted = None
            for name in top_dirs:
                candidate = os.path.join(work_dir, name)
                if os.path.isdir(candidate) and os.path.isdir(os.path.join(candidate, 'public_html')):
                    extracted = candidate
                    break
            if extracted is None:
                return False, 'Could not locate Roundcube files in archive'
            if extracted != ROUNDCUBE_ROOT:
                if os.path.isdir(ROUNDCUBE_ROOT):
                    shutil.rmtree(ROUNDCUBE_ROOT)
                shutil.move(extracted, ROUNDCUBE_ROOT)
    except Exception as exc:
        return False, 'Extract failed: %s' % exc
    finally:
        try:
            os.remove(archive)
        except OSError:
            pass
        for name in os.listdir(work_dir):
            if name.startswith('roundcubemail-') and os.path.isdir(os.path.join(work_dir, name)):
                try:
                    shutil.rmtree(os.path.join(work_dir, name))
                except Exception:
                    pass

    _write_config(existing_des_key)
    _ensure_runtime_dirs()

    if db_backup and os.path.isfile(db_backup):
        try:
            shutil.copy2(db_backup, ROUNDCUBE_SQLITE)
            os.remove(db_backup)
        except Exception:
            pass

    try:
        subprocess.run(['chown', '-R', 'lscpd:lscpd', ROUNDCUBE_ROOT], capture_output=True, timeout=120)
        subprocess.run(['find', ROUNDCUBE_ROOT, '-type', 'd', '-exec', 'chmod', '755', '{}', ';'], capture_output=True, timeout=180)
        subprocess.run(['find', ROUNDCUBE_ROOT, '-type', 'f', '-exec', 'chmod', '644', '{}', ';'], capture_output=True, timeout=180)
        os.chmod(ROUNDCUBE_CONFIG, 0o640)
    except Exception:
        pass

    settings = load_settings()
    settings['installed_version'] = version
    settings['last_deploy_at'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    save_settings(settings)
    return True, 'Roundcube %s deployed' % version


def ensure_ols_context():
    return ols_utils.ensure_ols_context()


def reload_lsws(restart=False):
    return ols_utils.reload_lsws(restart=restart)


def disable_serving():
    os.makedirs(ROUNDCUBE_ROOT, exist_ok=True)
    try:
        open(DISABLE_MARKER, 'w', encoding='utf-8').write('disabled\n')
    except Exception as exc:
        _log('WARNING: could not write disable marker: %s' % exc)
        return False
    deny_body = """# Roundcube disabled by roundcubeWebmail plugin
<IfModule mod_authz_core.c>
  Require all denied
</IfModule>
<IfModule !mod_authz_core.c>
  Order deny,allow
  Deny from all
</IfModule>
"""
    for target_dir in (ROUNDCUBE_PUBLIC, ROUNDCUBE_ROOT):
        if not os.path.isdir(target_dir):
            continue
        active_htaccess = os.path.join(target_dir, '.htaccess')
        backup = active_htaccess + '.cp-enabled-backup'
        try:
            if os.path.isfile(active_htaccess) and not os.path.isfile(backup):
                shutil.copy2(active_htaccess, backup)
            open(active_htaccess, 'w', encoding='utf-8').write(deny_body)
        except Exception as exc:
            _log('WARNING: disable_serving htaccess failed for %s: %s' % (target_dir, exc))
    reload_lsws(restart=True)
    return True


def enable_serving():
    try:
        if os.path.isfile(DISABLE_MARKER):
            os.remove(DISABLE_MARKER)
    except OSError:
        pass
    for target_dir in (ROUNDCUBE_PUBLIC, ROUNDCUBE_ROOT):
        active_htaccess = os.path.join(target_dir, '.htaccess')
        backup = active_htaccess + '.cp-enabled-backup'
        if os.path.isfile(backup):
            try:
                shutil.copy2(backup, active_htaccess)
            except Exception:
                pass
        elif os.path.isfile(active_htaccess):
            try:
                content = open(active_htaccess, 'r', encoding='utf-8', errors='replace').read()
                if 'disabled-by-plugin' in content or 'Require all denied' in content:
                    os.remove(active_htaccess)
            except Exception:
                pass
    ensure_ols_context()
    reload_lsws(restart=True)
    return True


def is_installed():
    return os.path.isfile(os.path.join(ROUNDCUBE_PUBLIC, 'index.php')) or os.path.isfile(os.path.join(ROUNDCUBE_ROOT, 'index.php'))


def verify_http(port=None):
    port = port or get_panel_port()
    url = 'https://127.0.0.1:%s/roundcube/' % port
    try:
        result = subprocess.run(
            ['curl', '-sk', '-o', '/tmp/roundcubeWebmail_verify.out', '-w', '%{http_code}', url],
            capture_output=True,
            text=True,
            timeout=30,
        )
        code = (result.stdout or '').strip()
        if result.returncode != 0:
            return False, 'curl failed'
        if code == '403':
            return False, 'HTTP 403 (disabled or denied)'
        if code not in ('200', '302', '301'):
            return False, 'HTTP %s' % code
        return True, 'OK (HTTP %s)' % code
    except Exception as exc:
        return False, str(exc)


def get_status(request=None):
    settings = load_settings()
    installed = is_installed()
    enabled = bool(settings.get('enabled', True)) and not os.path.isfile(DISABLE_MARKER)
    http_ok, http_detail = (False, 'not checked')
    if installed and enabled:
        http_ok, http_detail = verify_http()
    login_url = '/roundcube/'
    if request is not None:
        try:
            host = request.get_host()
            scheme = 'https' if request.is_secure() else 'http'
            login_url = '%s://%s/roundcube/' % (scheme, host)
        except Exception:
            pass
    return {
        'installed': installed,
        'enabled': enabled,
        'settings_enabled': bool(settings.get('enabled', True)),
        'installed_version': settings.get('installed_version') or '',
        'last_deploy_at': settings.get('last_deploy_at') or '',
        'public_path': ROUNDCUBE_PUBLIC if os.path.isdir(ROUNDCUBE_PUBLIC) else ROUNDCUBE_ROOT,
        'config_path': ROUNDCUBE_CONFIG,
        'imap_host': settings.get('imap_host') or 'localhost:993',
        'http_ok': http_ok,
        'http_detail': http_detail,
        'login_url': login_url,
        'disable_marker_present': os.path.isfile(DISABLE_MARKER),
    }


def post_install_tasks():
    ok, message = deploy_roundcube(force=False)
    if not ok:
        return False, message
    ensure_ols_context()
    settings = load_settings()
    settings['enabled'] = True
    save_settings(settings)
    enable_serving()
    return True, message


def pre_remove_tasks():
    settings = load_settings()
    settings['enabled'] = False
    save_settings(settings)
    disable_serving()
    return True, 'Roundcube serving stopped; files preserved at %s' % ROUNDCUBE_ROOT
