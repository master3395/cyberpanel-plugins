# -*- coding: utf-8 -*-
"""SnappyMail Webmail plugin utilities: deploy, OLS vhRoot, enable/disable, status."""
from __future__ import print_function

import json
import os
import re
import secrets
import shutil
import subprocess
import time

PLUGIN_NAME = 'snappymailWebmail'
SETTINGS_FILE = '/home/cyberpanel/plugins/snappymailWebmail_settings.json'
DISABLE_MARKER = '/usr/local/CyberCP/public/snappymail/.cp_webmail_disabled'

SNAPPY_PUBLIC = '/usr/local/CyberCP/public/snappymail'
SNAPPY_LSCP = '/usr/local/lscp/cyberpanel/snappymail'
SNAPPY_DATA = '/usr/local/lscp/cyberpanel/snappymail/data/'
SNAPPY_VERSION_FILE = '/etc/cyberpanel/snappymail_version'
SNAPPY_FALLBACK_VERSION = '2.38.2'

LSWS_ROOT = '/usr/local/lsws'
VHOST_DIR = os.path.join(LSWS_ROOT, 'conf', 'vhosts', 'CyberPanel')
VHOST_CONF = os.path.join(VHOST_DIR, 'vhost.conf')
HTTPD_CONFIG = os.path.join(LSWS_ROOT, 'conf', 'httpd_config.conf')
BIND_CONF = '/usr/local/lscp/conf/bind.conf'


def _log(msg):
    try:
        from plogical.CyberCPLogFileWriter import CyberCPLogFileWriter
        CyberCPLogFileWriter.writeToFile('[snappymailWebmail] ' + str(msg))
    except Exception:
        pass
    print('[snappymailWebmail] ' + str(msg))


def _default_settings():
    return {
        'enabled': True,
        'installed_version': '',
        'last_deploy_at': '',
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


def detect_lsphp_version():
    for ver in ('85', '84', '83', '82', '81', '80'):
        path = '/usr/local/lsws/lsphp%s/bin/lsphp' % ver
        if os.path.isfile(path):
            return ver
    return '83'


def get_panel_port():
    try:
        if os.path.isfile(BIND_CONF):
            line = open(BIND_CONF, 'r').read().strip()
            if line.startswith('*:'):
                port = line.split(':', 1)[1].strip().split()[0]
                if port.isdigit():
                    return port
    except Exception:
        pass
    return '8090'


def _copy_snappy_app_tree(src, dst):
    os.makedirs(dst, exist_ok=True)
    for name in os.listdir(src):
        if name == 'data':
            continue
        source = os.path.join(src, name)
        target = os.path.join(dst, name)
        if os.path.isdir(source):
            if os.path.isdir(target):
                shutil.rmtree(target)
            shutil.copytree(source, target)
        else:
            shutil.copy2(source, target)


def _ensure_snappy_data_path(include_path):
    if not os.path.isfile(include_path):
        return
    try:
        text = open(include_path, 'r', encoding='utf-8', errors='replace').read()
    except Exception:
        return
    needle = "define('APP_DATA_FOLDER_PATH', '%s');" % SNAPPY_DATA
    if needle in text:
        return
    if 'APP_DATA_FOLDER_PATH' in text:
        text = re.sub(
            r"define\(\s*'APP_DATA_FOLDER_PATH'\s*,\s*'[^']*'\s*\)\s*;",
            needle,
            text,
            count=1,
        )
    else:
        text = text.replace('<?php', "<?php\n" + needle, 1)
    try:
        open(include_path, 'w', encoding='utf-8').write(text)
    except Exception as exc:
        _log('WARNING: could not update %s: %s' % (include_path, exc))


def ensure_snappymail_public_tree():
    """Keep SnappyMail under CyberCP vhRoot (restrained=1 blocks /usr/local/lscp symlinks)."""
    public = SNAPPY_PUBLIC
    lscp = SNAPPY_LSCP
    index_public = os.path.join(public, 'index.php')
    index_lscp = os.path.join(lscp, 'index.php')

    try:
        if os.path.islink(public):
            target = os.path.realpath(public)
            _log('Replacing public/snappymail symlink with real tree (was -> %s)' % target)
            os.unlink(public)
            src = target if os.path.isfile(os.path.join(target, 'index.php')) else lscp
            if not os.path.isfile(os.path.join(src, 'index.php')):
                _log('WARNING: no SnappyMail source after removing symlink')
                return False
            _copy_snappy_app_tree(src, public)
        elif not os.path.isfile(index_public):
            if os.path.isfile(index_lscp):
                _log('Restoring public/snappymail from %s' % lscp)
                if os.path.isdir(public):
                    shutil.rmtree(public)
                _copy_snappy_app_tree(lscp, public)
            else:
                _log('WARNING: SnappyMail index.php missing under public and lscp')
                return False

        _ensure_snappy_data_path(os.path.join(public, 'include.php'))
        os.makedirs(SNAPPY_DATA, exist_ok=True)
        try:
            subprocess.run(
                ['chown', '-R', 'lscpd:lscpd', public, SNAPPY_DATA.rstrip('/')],
                capture_output=True,
                timeout=120,
            )
        except Exception:
            pass
        return os.path.isfile(index_public) and not os.path.islink(public)
    except Exception as exc:
        _log('ERROR ensure_snappymail_public_tree: %s' % exc)
        return False


def _resolve_snappy_version():
    version = SNAPPY_FALLBACK_VERSION
    if os.path.isfile(SNAPPY_VERSION_FILE):
        try:
            raw = open(SNAPPY_VERSION_FILE, 'r', encoding='utf-8').read().strip()
            if raw and len(raw) < 20 and all(ch.isdigit() or ch == '.' for ch in raw):
                version = raw
        except Exception:
            pass
    return version


def deploy_snappymail(force=False):
    """Download and deploy SnappyMail app files; preserve shared data directory."""
    os.makedirs('/usr/local/CyberCP/public', exist_ok=True)
    index_public = os.path.join(SNAPPY_PUBLIC, 'index.php')
    if os.path.isfile(index_public) and not force:
        ensure_snappymail_public_tree()
        return True, 'SnappyMail already deployed'

    version = _resolve_snappy_version()
    work_dir = '/usr/local/CyberCP/public'
    archive = os.path.join(work_dir, 'snappymail-%s.zip' % version)
    url = 'https://github.com/the-djmaze/snappymail/releases/download/v%s/snappymail-%s.zip' % (version, version)

    if not os.path.isfile(archive):
        result = subprocess.run(['wget', '-q', '-O', archive, url], capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            return False, 'Download failed: %s' % ((result.stderr or result.stdout or '').strip())

    if os.path.islink(SNAPPY_PUBLIC):
        os.unlink(SNAPPY_PUBLIC)
    elif os.path.isdir(SNAPPY_PUBLIC):
        shutil.rmtree(SNAPPY_PUBLIC)
    elif os.path.exists(SNAPPY_PUBLIC):
        os.remove(SNAPPY_PUBLIC)

    result = subprocess.run(
        ['unzip', '-q', archive, '-d', SNAPPY_PUBLIC],
        capture_output=True,
        text=True,
        timeout=300,
    )
    if result.returncode != 0:
        return False, 'Unzip failed: %s' % ((result.stderr or result.stdout or '').strip())

    try:
        os.remove(archive)
    except OSError:
        pass

    version_root = os.path.join(SNAPPY_PUBLIC, 'snappymail', 'v')
    if os.path.isdir(version_root):
        try:
            version_dirs = os.listdir(version_root)
            if version_dirs:
                include_path = os.path.join(version_root, version_dirs[0], 'include.php')
                if os.path.isfile(include_path):
                    lines = open(include_path, 'r', encoding='utf-8', errors='replace').readlines()
                    with open(include_path, 'w', encoding='utf-8') as handle:
                        for line in lines:
                            if "$sCustomDataPath = '';" in line:
                                handle.write("\t\t\t$sCustomDataPath = '%s';\n" % SNAPPY_DATA.rstrip('/'))
                            else:
                                handle.write(line)
        except Exception as exc:
            _log('WARNING: could not patch version include.php: %s' % exc)

    os.makedirs(os.path.join(SNAPPY_DATA, '_data_/_default_/configs'), exist_ok=True)
    ensure_snappymail_public_tree()

    settings = load_settings()
    settings['installed_version'] = version
    settings['last_deploy_at'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    save_settings(settings)
    return True, 'SnappyMail %s deployed' % version


def _php_app_context(path_prefix, location):
    return """
context %s {
  location                %s
  allowBrowse             1
  indexFiles              index.php
  addDefaultCharset       off
  scripthandler  {
    add                     lsapi:cyberpanelphp php
  }
}
""" % (path_prefix, location)


def _cyberpanelphp_ext_block(php_ver=None):
    php_ver = php_ver or detect_lsphp_version()
    return """
extprocessor cyberpanelphp {
  type                    lsapi
  address                 UDS://tmp/lshttpd/cyberpanelphp.sock
  maxConns                10
  env                     LSAPI_CHILDREN=10
  initTimeout             60
  retryTimeout            0
  persistConn             1
  respBuffer              0
  autoStart               2
  path                    /usr/local/lsws/lsphp%s/bin/lsphp
  extUser                 lscpd
  extGroup                lscpd
  memSoftLimit            2047M
  memHardLimit            2047M
  procSoftLimit           400
  procHardLimit           500
}
""" % php_ver


def patch_vhost_snappymail_context(vhost_path):
    if not os.path.isfile(vhost_path):
        return False
    try:
        content = open(vhost_path, 'r', encoding='utf-8', errors='replace').read()
    except Exception:
        return False

    changed = False
    if 'extprocessor cyberpanelphp' not in content:
        if 'extprocessor panelbackend' in content:
            content = content.replace('extprocessor panelbackend', _cyberpanelphp_ext_block() + '\nextprocessor panelbackend', 1)
        elif 'context /snappymail/' in content:
            content = content.replace('context /snappymail/', _cyberpanelphp_ext_block() + '\ncontext /snappymail/', 1)
        else:
            content = _cyberpanelphp_ext_block() + '\n' + content
        changed = True

    if 'context /snappymail/' not in content:
        insert = _php_app_context('/snappymail/', SNAPPY_PUBLIC + '/')
        if 'extprocessor panelbackend' in content:
            content = content.replace('extprocessor panelbackend', insert + '\nextprocessor panelbackend', 1)
        elif 'context /.well-known/acme-challenge' in content:
            content = content.replace('context /.well-known/acme-challenge', insert + '\ncontext /.well-known/acme-challenge', 1)
        else:
            content = insert + '\n' + content
        changed = True

    if changed:
        with open(vhost_path, 'w', encoding='utf-8') as handle:
            handle.write(content)
        _log('Patched SnappyMail OLS context: %s' % vhost_path)
    return True


def ensure_ols_context():
    os.makedirs(VHOST_DIR, exist_ok=True)
    patch_vhost_snappymail_context(VHOST_CONF)
    vhosts_root = os.path.join(LSWS_ROOT, 'conf', 'vhosts')
    if os.path.isdir(vhosts_root):
        for name in os.listdir(vhosts_root):
            if name in ('CyberPanel', 'Example'):
                continue
            patch_vhost_snappymail_context(os.path.join(vhosts_root, name, 'vhost.conf'))
    return True


def reload_lsws(restart=False):
    ctrl = os.path.join(LSWS_ROOT, 'bin', 'lswsctrl')
    if not os.path.isfile(ctrl):
        return False
    action = 'restart' if restart else 'reload'
    try:
        result = subprocess.run([ctrl, action], capture_output=True, text=True, timeout=120)
        return result.returncode == 0
    except Exception:
        return False


def disable_serving():
    os.makedirs(SNAPPY_PUBLIC, exist_ok=True)
    try:
        open(DISABLE_MARKER, 'w', encoding='utf-8').write('disabled\n')
    except Exception as exc:
        _log('WARNING: could not write disable marker: %s' % exc)
        return False
    deny_htaccess = os.path.join(SNAPPY_PUBLIC, '.htaccess.disabled-by-plugin')
    deny_body = """# SnappyMail disabled by snappymailWebmail plugin
<IfModule mod_authz_core.c>
  Require all denied
</IfModule>
<IfModule !mod_authz_core.c>
  Order deny,allow
  Deny from all
</IfModule>
"""
    try:
        open(deny_htaccess, 'w', encoding='utf-8').write(deny_body)
        active_htaccess = os.path.join(SNAPPY_PUBLIC, '.htaccess')
        if os.path.isfile(active_htaccess):
            backup = active_htaccess + '.cp-enabled-backup'
            if not os.path.isfile(backup):
                shutil.copy2(active_htaccess, backup)
        open(active_htaccess, 'w', encoding='utf-8').write(deny_body)
    except Exception as exc:
        _log('WARNING: disable_serving htaccess failed: %s' % exc)
    reload_lsws(restart=True)
    return True


def enable_serving():
    try:
        if os.path.isfile(DISABLE_MARKER):
            os.remove(DISABLE_MARKER)
    except OSError:
        pass
    active_htaccess = os.path.join(SNAPPY_PUBLIC, '.htaccess')
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
    ensure_snappymail_public_tree()
    ensure_ols_context()
    reload_lsws(restart=True)
    return True


def is_installed():
    return os.path.isfile(os.path.join(SNAPPY_PUBLIC, 'index.php'))


def verify_http(port=None):
    port = port or get_panel_port()
    url = 'https://127.0.0.1:%s/snappymail/index.php' % port
    try:
        result = subprocess.run(
            ['curl', '-sk', '-o', '/tmp/snappymailWebmail_verify.out', '-w', '%{http_code}', url],
            capture_output=True,
            text=True,
            timeout=30,
        )
        code = (result.stdout or '').strip()
        if result.returncode != 0:
            return False, 'curl failed'
        if code == '403':
            return False, 'HTTP 403 (disabled or denied)'
        if code != '200':
            return False, 'HTTP %s' % code
        return True, 'OK (HTTP 200)'
    except Exception as exc:
        return False, str(exc)


def get_status(request=None):
    settings = load_settings()
    installed = is_installed()
    enabled = bool(settings.get('enabled', True)) and not os.path.isfile(DISABLE_MARKER)
    http_ok, http_detail = (False, 'not checked')
    if installed and enabled:
        http_ok, http_detail = verify_http()
    login_url = '/snappymail/'
    if request is not None:
        try:
            host = request.get_host()
            scheme = 'https' if request.is_secure() else 'http'
            login_url = '%s://%s/snappymail/' % (scheme, host)
        except Exception:
            pass
    return {
        'installed': installed,
        'enabled': enabled,
        'settings_enabled': bool(settings.get('enabled', True)),
        'installed_version': settings.get('installed_version') or '',
        'last_deploy_at': settings.get('last_deploy_at') or '',
        'public_path': SNAPPY_PUBLIC,
        'data_path': SNAPPY_DATA.rstrip('/'),
        'http_ok': http_ok,
        'http_detail': http_detail,
        'login_url': login_url,
        'disable_marker_present': os.path.isfile(DISABLE_MARKER),
    }


def post_install_tasks():
    ok, message = deploy_snappymail(force=False)
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
    return True, 'SnappyMail serving stopped; data preserved at %s' % SNAPPY_DATA.rstrip('/')
