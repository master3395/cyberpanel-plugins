# -*- coding: utf-8 -*-
"""
Redis Manager - utility functions for Redis status and control.
"""
import subprocess
import shlex
import os
import re

REDIS_MARKER = '/home/cyberpanel/redis'
REDIS_SERVICE = 'redis'
REDIS_CLI = 'redis-cli'
REDIS_HOST = '127.0.0.1'
REDIS_PORT = '6379'

# Config file paths (try in order when no custom path set)
REDIS_CONF_PATHS = [
    '/etc/redis.conf',
    '/etc/redis/redis.conf',
    '/usr/local/etc/redis.conf',
    '/opt/redis/redis.conf',
    '/usr/local/redis/redis.conf',
    '/var/lib/redis/redis.conf',
    '/usr/local/CyberCP/redis/redis.conf',
]

# File where we store user-set config path (one line, absolute path)
REDIS_CUSTOM_PATH_FILE = '/home/cyberpanel/.redis_manager_config_path'

# Editable settings: key -> (label, type, default, help [, options for select]).
EDITABLE_CONFIG = {
    'bind': ('Bind address', 'text', '127.0.0.1', 'IP to bind (e.g. 127.0.0.1 or 0.0.0.0)'),
    'port': ('Port', 'number', '6379', 'TCP port (1-65535)'),
    'maxmemory': ('Max memory', 'text', '', 'Max memory (e.g. 256mb, 1gb). Empty = no limit.'),
    'maxmemory-policy': ('Max memory policy', 'select', 'noeviction',
        'Eviction policy when maxmemory is reached.',
        ['noeviction', 'allkeys-lru', 'volatile-lru', 'allkeys-lfu', 'volatile-lfu', 'volatile-ttl', 'volatile-random', 'allkeys-random']),
    'timeout': ('Client timeout (seconds)', 'number', '0', '0 = disabled'),
    'tcp-keepalive': ('TCP keepalive (seconds)', 'number', '300', ''),
    'requirepass': ('Password', 'password', '', 'Leave empty for no auth. Change requires Redis restart.'),
}


def is_installed():
    """Return True if Redis is installed (marker file exists)."""
    return os.path.exists(REDIS_MARKER)


def run_cmd(command, timeout=10):
    """Run shell command, return (success, output)."""
    try:
        result = subprocess.run(
            shlex.split(command),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        out = (result.stdout or '').strip() + (('\n' + (result.stderr or '').strip()) if result.stderr else '')
        return result.returncode == 0, out
    except subprocess.TimeoutExpired:
        return False, 'Command timed out'
    except Exception as e:
        return False, str(e)


def get_service_status():
    """Return status of Redis service: running, stopped, or not-installed."""
    if not is_installed():
        return 'not-installed', 'Redis is not installed. Install it from Manage Services.'
    # Run without shell redirections (run_cmd uses no shell; 2>/dev/null would be passed as unit name)
    ok, out = run_cmd('systemctl is-active %s' % REDIS_SERVICE)
    if not ok:
        # Unit not found or error -> treat as stopped/unknown
        out_lower = (out or '').strip().lower()
        if 'could not find' in out_lower or 'not-found' in out_lower or 'no such file' in out_lower:
            return 'stopped', 'Stopped (unit not found)'
        return 'unknown', out or 'Could not determine status'
    out = out.strip().lower()
    if out == 'active':
        return 'running', 'Running'
    if out == 'inactive' or out == 'failed':
        return 'stopped', 'Stopped'
    return 'unknown', out


def service_control(action):
    """Start, stop, or restart Redis. action: start, stop, restart."""
    if action not in ('start', 'stop', 'restart'):
        return False, 'Invalid action'
    if not is_installed():
        return False, 'Redis is not installed.'
    ok, out = run_cmd('systemctl %s %s' % (action, REDIS_SERVICE), timeout=30)
    return ok, out


def get_redis_info():
    """Return Redis INFO output or error message."""
    if not is_installed():
        return None, 'Redis is not installed.'
    # No shell redirections (run_cmd uses no shell; stderr is captured by subprocess)
    ok, out = run_cmd('%s -h %s -p %s INFO' % (REDIS_CLI, REDIS_HOST, REDIS_PORT))
    if not ok:
        return None, out or 'Could not connect to Redis.'
    return out, None


def redis_flush_all():
    """Run FLUSHALL. Returns (success, message)."""
    if not is_installed():
        return False, 'Redis is not installed.'
    ok, out = run_cmd('%s -h %s -p %s FLUSHALL' % (REDIS_CLI, REDIS_HOST, REDIS_PORT))
    if ok and 'OK' in out:
        return True, 'Cache flushed successfully.'
    return False, out or 'Flush failed.'


def get_custom_config_path():
    """Return user-set config path if set and file exists, else None."""
    try:
        if os.path.isfile(REDIS_CUSTOM_PATH_FILE):
            with open(REDIS_CUSTOM_PATH_FILE, 'r') as f:
                path = (f.read() or '').strip()
            if path and os.path.isfile(path):
                return path
    except (IOError, OSError):
        pass
    return None


def set_custom_config_path(path):
    """Save custom config path. path=None or '' clears it. Returns (success, message)."""
    path = (path or '').strip()
    try:
        if path:
            if not os.path.isfile(path):
                return False, 'File does not exist: %s' % path
            dirname = os.path.dirname(REDIS_CUSTOM_PATH_FILE)
            if dirname and not os.path.isdir(dirname):
                os.makedirs(dirname, mode=0o700)
            with open(REDIS_CUSTOM_PATH_FILE, 'w') as f:
                f.write(os.path.abspath(path) + '\n')
        else:
            if os.path.isfile(REDIS_CUSTOM_PATH_FILE):
                os.remove(REDIS_CUSTOM_PATH_FILE)
        return True, 'Config path saved.' if path else 'Config path cleared.'
    except (IOError, OSError) as e:
        return False, str(e)


def _config_path_from_cmdline(cmdline_str):
    """From null-separated cmdline string, find first path that looks like a .conf file."""
    if not cmdline_str:
        return None
    parts = cmdline_str.replace('\x00', ' ').split()
    for p in parts:
        p = p.strip()
        if p.endswith('.conf') and p.startswith('/') and len(p) > 5:
            if os.path.isfile(p):
                return p
    return None


def detect_redis_config_path():
    """Auto-detect config path: Redis INFO config_file, then process cmdline, systemd, paths, find."""
    # 0) From Redis INFO (when Redis is running, most authoritative)
    info_text, info_err = get_redis_info()
    if info_text:
        for line in info_text.splitlines():
            line = line.strip()
            if line.startswith('config_file:'):
                path = line.split(':', 1)[1].strip()
                if path:
                    return path  # Use Redis-reported path even if we can't stat it (e.g. permission)
                break

    # 1) From running Redis process (cmdline)
    try:
        result = subprocess.run(
            ['pgrep', '-f', 'redis-server'],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout:
            pids = result.stdout.strip().split()
            for pid in pids:
                pid = pid.strip()
                if not pid:
                    continue
                cmdline_path = '/proc/%s/cmdline' % pid
                if os.path.isfile(cmdline_path):
                    with open(cmdline_path, 'r') as f:
                        cmdline = f.read()
                    path = _config_path_from_cmdline(cmdline)
                    if path:
                        return path
    except (OSError, IOError, subprocess.TimeoutExpired):
        pass

    # 2) Systemd: try known unit names first, then list all redis* units
    for unit in (REDIS_SERVICE, 'redis-server', 'redis-server.service', 'redis.service'):
        ok, out = run_cmd('systemctl show %s --property=ExecStart --no-pager' % unit)
        if ok and out:
            # ExecStart=/usr/bin/redis-server /etc/redis/redis.conf or /usr/bin/redis-server /etc/redis/redis.conf --supervised systemd
            m = re.search(r'redis-server\s+(\S+)', out)
            if m:
                path = m.group(1).strip()
                if path.startswith('"') and path.endswith('"'):
                    path = path[1:-1]
                if path.endswith('.conf') and os.path.isfile(path):
                    return path
                # might be path with trailing args in same token
                if path.endswith('.conf'):
                    if os.path.isfile(path):
                        return path
                else:
                    # take only the path part (first token after redis-server)
                    path = path.split()[0] if path.split() else path
                    if path.endswith('.conf') and os.path.isfile(path):
                        return path

    # 2b) List all unit files, find redis* and check ExecStart
    ok, out = run_cmd('systemctl list-unit-files --no-legend --no-pager')
    if ok and out:
        for line in out.splitlines():
            line = line.strip()
            if not line or 'redis' not in line.lower():
                continue
            parts = line.split()
            if not parts:
                continue
            unit = parts[0]
            if not unit.endswith('.service'):
                unit = unit + '.service'
            ok2, out2 = run_cmd('systemctl show %s --property=ExecStart --no-pager' % unit)
            if ok2 and out2:
                m = re.search(r'redis-server\s+(\S+)', out2)
                if m:
                    path = m.group(1).strip().strip('"')
                    if path.endswith('.conf') and os.path.isfile(path):
                        return path

    # 3) Fallback: try common paths
    for path in REDIS_CONF_PATHS:
        if os.path.isfile(path):
            return path

    # 4) Search filesystem for redis.conf (limited scope, no shell)
    try:
        result = subprocess.run(
            ['find', '/etc', '/usr/local', '/opt', '/var', '-name', 'redis.conf', '-type', 'f', '-readable'],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0 and result.stdout:
            for line in result.stdout.strip().splitlines():
                path = line.strip()
                if path and os.path.isfile(path):
                    return path
    except (OSError, subprocess.TimeoutExpired):
        pass
    return None


def get_redis_config_path():
    """Return path to redis.conf: custom path first, then auto-detect, then REDIS_CONF_PATHS."""
    custom = get_custom_config_path()
    if custom:
        return custom
    detected = detect_redis_config_path()
    if detected:
        return detected
    return None


def get_paths_tried_for_message():
    """Return list of paths we consider (for error message)."""
    paths = []
    try:
        if os.path.isfile(REDIS_CUSTOM_PATH_FILE):
            with open(REDIS_CUSTOM_PATH_FILE, 'r') as f:
                p = (f.read() or '').strip()
            if p:
                paths.append(p)
    except (IOError, OSError):
        pass
    paths.extend(REDIS_CONF_PATHS)
    return paths


# Allowed prefixes for config path when fixing permissions (realpath must start with one)
REDIS_CONF_ALLOWED_PREFIXES = ('/etc/', '/usr/local/', '/opt/', '/var/')


def fix_redis_config_permissions(path):
    """Make redis.conf readable by the panel. path must be under allowed prefixes. Returns (success, message)."""
    path = (path or '').strip()
    if not path:
        return False, 'No path specified.'
    if not os.path.isfile(path):
        return False, 'File does not exist: %s' % path
    try:
        real = os.path.realpath(path)
    except (OSError, IOError):
        real = path
    if not real.endswith('.conf'):
        return False, 'Path must be a .conf file.'
    if not any(real.startswith(prefix) for prefix in REDIS_CONF_ALLOWED_PREFIXES):
        return False, 'Path not in an allowed directory (etc, usr/local, opt, var).'
    try:
        os.chmod(real, 0o644)
    except (OSError, IOError) as e:
        return False, 'Could not chmod file: %s' % str(e)
    parent = os.path.dirname(real)
    if parent and os.path.isdir(parent):
        try:
            os.chmod(parent, 0o755)
        except (OSError, IOError):
            pass
    return True, 'Permissions set to 644. Reload the page to read the config.'


def _parse_redis_conf(path):
    """Parse redis.conf; return dict of key -> value (only first occurrence per key)."""
    out = {}
    if not path or not os.path.isfile(path):
        return out
    try:
        with open(path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                # key value or key "value"
                m = re.match(r'^(\S+)\s+(.+)$', line)
                if m:
                    key, val = m.group(1).strip(), m.group(2).strip()
                    if key not in out:
                        if val.startswith('"') and val.endswith('"'):
                            val = val[1:-1].replace('\\"', '"')
                        out[key] = val
    except (IOError, OSError):
        pass
    return out


def get_editable_config_defaults():
    """Return dict of editable config keys to their default values (for Reset/Default button)."""
    return {k: (item[2] if item[2] is not None else '') for k, item in EDITABLE_CONFIG.items()}


def get_editable_config_form_defaults():
    """Return same structure as get_editable_config() result but with all values set to defaults (for when config file is missing)."""
    result = {}
    for key, item in EDITABLE_CONFIG.items():
        label, typ, default, help_text = item[0], item[1], item[2], item[3]
        options = item[4] if len(item) > 4 else []
        result[key] = {
            'value': default if default is not None else '',
            'label': label,
            'type': typ,
            'default': default,
            'help': help_text,
            'options': options,
        }
    return result


def get_editable_config():
    """Return (result_dict, config_path, error_message, read_warning). read_warning set when path exists but file could not be read."""
    path = get_redis_config_path()
    if not path:
        paths_tried = get_paths_tried_for_message()
        return {}, None, 'Redis config file not found. Paths checked: %s. Set a custom path below or use Auto-detect.' % ', '.join(paths_tried), None
    parsed = _parse_redis_conf(path)
    read_warning = None
    if not parsed and path:
        read_warning = 'Config file at %s could not be read (permission or missing). Showing defaults. Fix file permissions if needed.' % path
    result = {}
    for key, item in EDITABLE_CONFIG.items():
        label = item[0]
        typ = item[1]
        default = item[2]
        help_text = item[3]
        options = item[4] if len(item) > 4 else []
        result[key] = {
            'value': parsed.get(key, default) if default else parsed.get(key, ''),
            'label': label,
            'type': typ,
            'default': default,
            'help': help_text,
            'options': options,
        }
    return result, path, None, read_warning


def _validate_config_value(key, value):
    """Validate a single config value. Return (ok, error_message)."""
    if key not in EDITABLE_CONFIG:
        return False, 'Unknown key'
    item = EDITABLE_CONFIG[key]
    typ = item[1]
    default = item[2]
    if typ == 'number':
        if value is None or str(value).strip() == '':
            return True, None
        try:
            n = int(value)
            if key == 'port' and (n < 1 or n > 65535):
                return False, 'Port must be 1-65535'
            if key in ('timeout', 'tcp-keepalive') and n < 0:
                return False, 'Must be >= 0'
        except ValueError:
            return False, 'Must be a number'
    if typ == 'password':
        # Allow any string; empty = no password
        pass
    return True, None


def save_redis_config(settings_dict):
    """Update redis.conf with only whitelisted keys. Returns (success, message)."""
    path = get_redis_config_path()
    if not path:
        return False, 'Redis config file not found.'
    try:
        with open(path, 'r') as f:
            lines = f.readlines()
    except (IOError, OSError) as e:
        return False, 'Cannot read config: %s' % str(e)
    # Build set of keys we're updating
    updates = {}
    for key in EDITABLE_CONFIG:
        if key in settings_dict:
            val = settings_dict[key]
            if val is None:
                val = ''
            val = str(val).strip()
            ok, err = _validate_config_value(key, val)
            if not ok:
                return False, '%s: %s' % (key, err or 'invalid')
            updates[key] = val
    # Rewrite file: replace existing key lines, keep others
    key_written = set()
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            new_lines.append(line)
            continue
        m = re.match(r'^(\S+)\s+', stripped)
        if m:
            k = m.group(1)
            if k in updates:
                key_written.add(k)
                val = updates[k]
                if val and ' ' in val:
                    new_lines.append('%s "%s"\n' % (k, val.replace('"', '\\"')))
                else:
                    new_lines.append('%s %s\n' % (k, val if val else '""'))
                continue
        new_lines.append(line)
    # Append any key we didn't replace
    for k, val in updates.items():
        if k not in key_written:
            if val and ' ' in val:
                new_lines.append('%s "%s"\n' % (k, val.replace('"', '\\"')))
            else:
                new_lines.append('%s %s\n' % (k, val if val else '""'))
    try:
        with open(path, 'w') as f:
            f.writelines(new_lines)
    except (IOError, OSError) as e:
        return False, 'Cannot write config: %s' % str(e)
    return True, 'Settings saved. Restart Redis for changes to take effect.'
