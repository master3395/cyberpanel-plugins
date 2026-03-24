# -*- coding: utf-8 -*-
"""
Fernet key storage for encrypted MySQL passwords (same pattern as CyberPanel phpMyAdmin flow).

The CyberPanel WSGI process runs as user ``cyberpanel``; the key must be readable by that
user (mode 600, owner cyberpanel). Do NOT chown to root — that breaks encrypt/decrypt.
"""
import os
import pwd

from cryptography.fernet import Fernet


KEY_BASENAME = 'limitedPhpmyAdmin_fernet.key'
KEY_DIR = '/home/cyberpanel'
_PANEL_USER = 'cyberpanel'


def _key_path():
    return os.path.join(KEY_DIR, KEY_BASENAME)


def _chown_key_to_panel(path):
    """Make key file readable by lswsgi (cyberpanel). Safe no-op if user missing or not root."""
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
    try:
        ent = pwd.getpwnam(_PANEL_USER)
        os.chown(path, ent.pw_uid, ent.pw_gid)
    except (OSError, KeyError):
        pass


def get_cipher():
    """
    Return Fernet instance; creates key file with safe permissions if missing.
    """
    path = _key_path()
    if not os.path.isdir(KEY_DIR):
        try:
            os.makedirs(KEY_DIR, mode=0o700)
        except OSError:
            pass
    if not os.path.isfile(path):
        key = Fernet.generate_key()
        try:
            with open(path, 'wb') as f:
                f.write(key)
            _chown_key_to_panel(path)
        except OSError:
            raise RuntimeError('Cannot create Fernet key at %s' % path)
    try:
        with open(path, 'rb') as f:
            return Fernet(f.read())
    except OSError as exc:
        raise RuntimeError(
            'Cannot read Fernet key at %s (fix: chown %s:%s and chmod 600)'
            % (path, _PANEL_USER, _PANEL_USER)
        ) from exc


def encrypt_password(plain_password):
    if plain_password is None:
        plain_password = ''
    c = get_cipher()
    return c.encrypt(plain_password.encode('utf-8')).decode('utf-8')


def decrypt_password(stored):
    if not stored:
        return ''
    c = get_cipher()
    return c.decrypt(stored.encode('utf-8')).decode('utf-8')
