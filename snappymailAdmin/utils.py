# -*- coding: utf-8 -*-
"""
SnappyMail Admin Password plugin – set admin password via SnappyMail API.
"""
import os
import re
import tempfile
import subprocess
import stat

# Paths used by CyberPanel SnappyMail
SNAPPYMAIL_INDEX = '/usr/local/CyberCP/public/snappymail/index.php'
SNAPPYMAIL_DATA = '/usr/local/lscp/cyberpanel/snappymail/data'
SNAPPYMAIL_APPLICATION_INI = '/usr/local/lscp/cyberpanel/snappymail/data/_data_/_default_/configs/application.ini'
PHP_BIN = '/usr/local/lsws/lsphp83/bin/php'
# Fallback if lsphp83 not present
PHP_ALTERNATIVES = ['/usr/local/lsws/lsphp82/bin/php', '/usr/local/lsws/lsphp81/bin/php', '/usr/bin/php']


def _get_php_bin():
    if os.path.isfile(PHP_BIN) and os.access(PHP_BIN, os.X_OK):
        return PHP_BIN
    for p in PHP_ALTERNATIVES:
        if os.path.isfile(p) and os.access(p, os.X_OK):
            return p
    return None


def is_snappymail_available():
    """Return True if SnappyMail is installed and API is usable."""
    if not os.path.isfile(SNAPPYMAIL_INDEX):
        return False
    if not os.path.isdir(SNAPPYMAIL_DATA):
        return False
    return _get_php_bin() is not None


def get_snappymail_admin_login():
    """Return the current SnappyMail admin login (username), or 'admin' if not set."""
    try:
        if not os.path.isfile(SNAPPYMAIL_APPLICATION_INI):
            return 'admin'
        with open(SNAPPYMAIL_APPLICATION_INI, 'r', encoding='utf-8', errors='replace') as f:
            in_security = False
            for line in f:
                line = line.strip()
                if line == '[security]':
                    in_security = True
                    continue
                if in_security:
                    if line.startswith('['):
                        break
                    if line.startswith('admin_login'):
                        # admin_login = "value" or admin_login = value
                        eq = line.find('=')
                        if eq >= 0:
                            val = line[eq + 1:].strip().strip('"').strip("'")
                            return val or 'admin'
    except (OSError, IOError):
        pass
    return 'admin'


def set_snappymail_admin_password(new_password, admin_login=None):
    """
    Set the SnappyMail Admin panel password (and optionally the admin username).
    Uses a temp file for the password so it is not written into the PHP source.
    admin_login: if provided, sets the admin username (e.g. 'admin' or custom).
    Returns (success: bool, message: str).
    """
    if not new_password or not isinstance(new_password, str):
        return False, 'Password is required.'
    pwd = new_password.strip()
    if len(pwd) < 6:
        return False, 'Password must be at least 6 characters.'
    if len(pwd) > 512:
        return False, 'Password is too long.'
    # Disallow control characters and null
    if re.search(r'[\x00-\x1f\x7f]', pwd):
        return False, 'Password contains invalid characters.'

    # Preserve or set admin username (SnappyMail config always gets admin_login set)
    if admin_login is not None and isinstance(admin_login, str):
        login_val = admin_login.strip() or 'admin'
        if len(login_val) > 64:
            return False, 'Admin username must be at most 64 characters.'
        if not re.match(r'^[a-zA-Z0-9_\-]+$', login_val):
            return False, 'Admin username may only contain letters, numbers, underscore and hyphen.'
    else:
        login_val = get_snappymail_admin_login()

    php_bin = _get_php_bin()
    if not php_bin:
        return False, 'PHP binary not found. Is LiteSpeed PHP installed?'

    if not os.path.isfile(SNAPPYMAIL_INDEX):
        return False, 'SnappyMail is not installed at the expected path.'

    pass_file = None
    script_file = None
    try:
        fd, pass_file = tempfile.mkstemp(prefix='snappymail_admin_pass_', dir='/tmp')
        try:
            os.write(fd, pwd.encode('utf-8'))
        finally:
            os.close(fd)
        os.chmod(pass_file, stat.S_IRUSR | stat.S_IWUSR)

        # PHP script: buffer all output from SnappyMail include, then output only Done/Error or a specific error
        script_content = """<?php
ob_start();
$_ENV['snappymail_INCLUDE_AS_API'] = true;
$passFile = getenv('SNAPPYMAIL_PASS_FILE');
if (!$passFile || !is_readable($passFile)) { ob_end_clean(); echo 'Error: pass file'; exit(1); }
$password = trim(file_get_contents($passFile));
@unlink($passFile);
$adminLogin = trim(getenv('SNAPPYMAIL_ADMIN_LOGIN') ?: '');
if ($adminLogin === '') { $adminLogin = 'admin'; }
include '%s';
$oConfig = \\RainLoop\\Api::Config();
$oConfig->Set('security', 'admin_login', $adminLogin);
$oConfig->SetPassword(new \\SnappyMail\\SensitiveString($password));
if (defined('APP_PRIVATE_DATA')) {
    $configFile = APP_PRIVATE_DATA . 'configs/application.ini';
    if (file_exists($configFile) && !is_writable($configFile)) {
        ob_end_clean(); echo 'Error: config not writable'; exit(1);
    }
}
$ok = $oConfig->Save();
ob_end_clean();
echo $ok ? 'Done' : 'Error';
""" % SNAPPYMAIL_INDEX.replace("'", "\\'")

        snappymail_dir = os.path.dirname(SNAPPYMAIL_INDEX)
        fd2, script_file = tempfile.mkstemp(prefix='snappymail_setpass_', suffix='.php', dir='/tmp')
        try:
            os.write(fd2, script_content.encode('utf-8'))
        finally:
            os.close(fd2)
        os.chmod(script_file, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)

        env = os.environ.copy()
        env['SNAPPYMAIL_PASS_FILE'] = pass_file
        env['SNAPPYMAIL_ADMIN_LOGIN'] = login_val
        result = subprocess.run(
            [php_bin, script_file],
            env=env,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=30,
            cwd=snappymail_dir,  # so SnappyMail path resolution does not use /tmp
        )
        out = (result.stdout or '').strip()
        err = (result.stderr or '').strip()
        if result.returncode != 0:
            return False, err or out or 'PHP script failed (code %s).' % result.returncode
        # With ob_end_clean() we expect only "Done" or "Error" (or a specific error message)
        if out != 'Done':
            if out == 'Error':
                msg = (
                    'SnappyMail could not save the password. '
                    'Ensure the data folder is writable: run on the server '
                    'sudo bash /usr/local/CyberCP/snappymailAdmin/fix_snappymail_permissions.sh'
                )
            else:
                msg = err or out or 'SnappyMail API did not return success.'
            return False, msg

        # Verify the config file on disk was actually updated (same file the web UI reads)
        actual_login = get_snappymail_admin_login()
        if actual_login != login_val:
            try:
                from plogical.CyberCPLogFileWriter import CyberCPLogFileWriter as logging
                logging.writeToFile(
                    'snappymailAdmin: PHP reported Done but config has admin_login=%r (expected %r). '
                    'Config path: %s' % (actual_login, login_val, SNAPPYMAIL_APPLICATION_INI)
                )
            except Exception:
                pass
            return False, (
                'SnappyMail reported success but the config file was not updated. '
                'The admin panel may be using a different config path. '
                'Try running: sudo bash /usr/local/CyberCP/snappymailAdmin/fix_snappymail_permissions.sh'
            )
        return True, 'SnappyMail Admin credentials updated. Log in at the Admin URL shown above with username "%s" and your new password.' % login_val
    except subprocess.TimeoutExpired:
        return False, 'Request timed out.'
    except Exception as e:
        try:
            from plogical.CyberCPLogFileWriter import CyberCPLogFileWriter as logging
            logging.writeToFile('snappymailAdmin set_snappymail_admin_password: %s' % str(e))
        except Exception:
            pass
        return False, str(e)
    finally:
        for f in (pass_file, script_file):
            if f and os.path.isfile(f):
                try:
                    os.unlink(f)
                except OSError:
                    pass
