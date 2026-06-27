# -*- coding: utf-8 -*-
import os
import shutil
import secrets
import string
import subprocess


POSTGRES_SERVICE_CANDIDATES = (
    'postgresql',
    'postgresql-16',
    'postgresql-15',
    'postgresql-14',
    'postgresql-13',
    'postgresql@16-main',
    'postgresql@15-main',
    'postgresql@14-main',
    'postgresql@13-main',
)
PSQL_CANDIDATES = (
    '/usr/bin/psql',
    '/usr/pgsql-16/bin/psql',
    '/usr/pgsql-15/bin/psql',
    '/usr/pgsql-14/bin/psql',
    '/usr/pgsql-13/bin/psql',
    'psql',
)
CREATEDB_CANDIDATES = (
    '/usr/bin/createdb',
    '/usr/pgsql-16/bin/createdb',
    '/usr/pgsql-15/bin/createdb',
    '/usr/pgsql-14/bin/createdb',
    '/usr/pgsql-13/bin/createdb',
    'createdb',
)
STATE_DIR = '/usr/local/CyberCP/pluginState/postgresManager'
PASSWORD_FILE = os.path.join(STATE_DIR, 'cyberpanel_pgadmin_password')
ADMIN_ROLE = 'cyberpanel_pgadmin'
ADMIN_DB = 'cyberpanel_postgres'
ADMINER_DIR = '/usr/local/CyberCP/public/postgres-adminer'


def run_cmd(args, timeout=20, user=None):
    cmd = list(args)
    if user:
        cmd = ['runuser', '-u', user, '--'] + cmd
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        out = (result.stdout or '').strip()
        err = (result.stderr or '').strip()
        if err:
            out = (out + '\n' + err).strip()
        return result.returncode == 0, out
    except subprocess.TimeoutExpired:
        return False, 'Command timed out.'
    except OSError as exc:
        return False, str(exc)


def _first_existing(candidates):
    for item in candidates:
        if item.startswith('/') and os.path.exists(item):
            return item
        if not item.startswith('/') and shutil.which(item):
            return item
    return candidates[-1]


def psql_bin():
    return _first_existing(PSQL_CANDIDATES)


def createdb_bin():
    return _first_existing(CREATEDB_CANDIDATES)


def is_installed():
    ok, _ = run_cmd([psql_bin(), '--version'], timeout=5)
    return ok


def detect_service():
    for service in POSTGRES_SERVICE_CANDIDATES:
        ok, out = run_cmd(['systemctl', 'status', service, '--no-pager'], timeout=5)
        if ok or 'Loaded: loaded' in (out or '') or 'Active:' in (out or ''):
            return service
    return 'postgresql'


def get_service_status():
    if not is_installed():
        return 'not-installed', 'PostgreSQL is not installed.'
    service = detect_service()
    ok, out = run_cmd(['systemctl', 'is-active', service], timeout=5)
    if ok and out.strip() == 'active':
        return 'running', 'Running (%s)' % service
    if out.strip() in ('inactive', 'failed'):
        return 'stopped', 'Stopped (%s)' % service
    return 'unknown', (out or 'Unknown') + ' (%s)' % service


def service_control(action):
    if action not in ('start', 'stop', 'restart'):
        return False, 'Invalid action.'
    if not is_installed():
        return False, 'PostgreSQL is not installed. Run install.sh first.'
    service = detect_service()
    ok, out = run_cmd(['systemctl', action, service], timeout=45)
    return ok, out or ('PostgreSQL %sed.' % action)


def postgres_version():
    ok, out = run_cmd([psql_bin(), '--version'], timeout=5)
    return out if ok else ''


def get_listen_addresses():
    ok, out = run_cmd(['ss', '-ltn'], timeout=5)
    if not ok:
        return ''
    return '\n'.join([line for line in out.splitlines() if ':5432' in line])


def adminer_installed():
    return os.path.exists(os.path.join(ADMINER_DIR, 'index.php'))


def get_admin_password():
    try:
        with open(PASSWORD_FILE, 'r') as f:
            return (f.read() or '').strip()
    except IOError:
        return ''


def _generate_password(length=32):
    alphabet = string.ascii_letters + string.digits + '_-.'
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def ensure_admin_credentials():
    if not os.path.isdir(STATE_DIR):
        os.makedirs(STATE_DIR, 0o700)
    password = get_admin_password() or _generate_password()
    if not os.path.exists(PASSWORD_FILE):
        with open(PASSWORD_FILE, 'w') as f:
            f.write(password + '\n')
        os.chmod(PASSWORD_FILE, 0o600)

    sql = (
        "DO $$ BEGIN "
        "IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '%s') THEN "
        "CREATE ROLE %s WITH LOGIN CREATEDB CREATEROLE PASSWORD '%s'; "
        "ELSE ALTER ROLE %s WITH LOGIN CREATEDB CREATEROLE PASSWORD '%s'; "
        "END IF; END $$;"
    ) % (ADMIN_ROLE, ADMIN_ROLE, password.replace("'", "''"), ADMIN_ROLE, password.replace("'", "''"))
    ok, out = run_cmd([psql_bin(), '-v', 'ON_ERROR_STOP=1', '-c', sql], timeout=20, user='postgres')
    if not ok:
        return False, out
    ok, out = run_cmd(
        [psql_bin(), '-Atqc', "SELECT 1 FROM pg_database WHERE datname='%s'" % ADMIN_DB],
        timeout=10,
        user='postgres',
    )
    if ok and out.strip() == '1':
        return True, 'Admin role and database are ready.'
    ok, out = run_cmd([createdb_bin(), '-O', ADMIN_ROLE, ADMIN_DB], timeout=20, user='postgres')
    return ok, out or 'Admin role and database are ready.'


def admin_context(request):
    scheme = 'https' if request.is_secure() else 'http'
    return {
        'adminer_url': '%s://%s/postgres-adminer/' % (scheme, request.get_host()),
        'admin_user': ADMIN_ROLE,
        'admin_database': ADMIN_DB,
        'admin_password': get_admin_password(),
        'adminer_installed': adminer_installed(),
    }
