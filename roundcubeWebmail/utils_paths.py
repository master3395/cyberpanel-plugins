# -*- coding: utf-8 -*-
"""Shared paths and helpers for Roundcube Webmail plugin."""
from __future__ import print_function

import os

PLUGIN_NAME = 'roundcubeWebmail'
SETTINGS_FILE = '/home/cyberpanel/plugins/roundcubeWebmail_settings.json'
DISABLE_MARKER = '/usr/local/CyberCP/public/roundcube/.cp_webmail_disabled'

ROUNDCUBE_ROOT = '/usr/local/CyberCP/public/roundcube'
ROUNDCUBE_PUBLIC = os.path.join(ROUNDCUBE_ROOT, 'public_html')
ROUNDCUBE_CONFIG = os.path.join(ROUNDCUBE_ROOT, 'config', 'config.inc.php')
ROUNDCUBE_DB_DIR = os.path.join(ROUNDCUBE_ROOT, 'db')
ROUNDCUBE_SQLITE = os.path.join(ROUNDCUBE_DB_DIR, 'roundcube.db')
ROUNDCUBE_VERSION_FILE = '/etc/cyberpanel/roundcube_version'
ROUNDCUBE_FALLBACK_VERSION = '1.6.9'

LSWS_ROOT = '/usr/local/lsws'
VHOST_DIR = os.path.join(LSWS_ROOT, 'conf', 'vhosts', 'CyberPanel')
VHOST_CONF = os.path.join(VHOST_DIR, 'vhost.conf')
BIND_CONF = '/usr/local/lscp/conf/bind.conf'


def _log(msg):
    try:
        from plogical.CyberCPLogFileWriter import CyberCPLogFileWriter
        CyberCPLogFileWriter.writeToFile('[roundcubeWebmail] ' + str(msg))
    except Exception:
        pass
    print('[roundcubeWebmail] ' + str(msg))


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
