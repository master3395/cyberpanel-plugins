# -*- coding: utf-8 -*-
"""
Fernet key storage for encrypted MySQL passwords (same pattern as CyberPanel phpMyAdmin flow).
"""
import os

from cryptography.fernet import Fernet
from plogical.processUtilities import ProcessUtilities


KEY_BASENAME = 'limitedPhpmyAdmin_fernet.key'
KEY_DIR = '/home/cyberpanel'


def _key_path():
    return os.path.join(KEY_DIR, KEY_BASENAME)


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
            try:
                ProcessUtilities.executioner('chown root:root %s' % path)
                ProcessUtilities.executioner('chmod 600 %s' % path)
            except Exception:
                pass
        except OSError:
            raise RuntimeError('Cannot create Fernet key at %s' % path)
    with open(path, 'rb') as f:
        return Fernet(f.read())


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
