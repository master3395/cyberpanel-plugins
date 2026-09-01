# -*- coding: utf-8 -*-
"""Roundcube Webmail OLS helpers."""
from __future__ import print_function

import os
import subprocess

from .utils_paths import (
    LSWS_ROOT,
    VHOST_DIR,
    VHOST_CONF,
    ROUNDCUBE_ROOT,
    ROUNDCUBE_PUBLIC,
    detect_lsphp_version,
    _log,
)

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


def patch_vhost_roundcube_context(vhost_path):
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
        elif 'context /roundcube/' in content:
            content = content.replace('context /roundcube/', _cyberpanelphp_ext_block() + '\ncontext /roundcube/', 1)
        else:
            content = _cyberpanelphp_ext_block() + '\n' + content
        changed = True

    location = ROUNDCUBE_PUBLIC + '/'
    if not os.path.isdir(ROUNDCUBE_PUBLIC):
        location = ROUNDCUBE_ROOT + '/'

    if 'context /roundcube/' not in content:
        insert = _php_app_context('/roundcube/', location)
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
        _log('Patched Roundcube OLS context: %s' % vhost_path)
    return True


def ensure_ols_context():
    os.makedirs(VHOST_DIR, exist_ok=True)
    patch_vhost_roundcube_context(VHOST_CONF)
    vhosts_root = os.path.join(LSWS_ROOT, 'conf', 'vhosts')
    if os.path.isdir(vhosts_root):
        for name in os.listdir(vhosts_root):
            if name in ('CyberPanel', 'Example'):
                continue
            patch_vhost_roundcube_context(os.path.join(vhosts_root, name, 'vhost.conf'))
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


