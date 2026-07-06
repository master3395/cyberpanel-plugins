# -*- coding: utf-8 -*-
import os
import json
import re
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
DATABASES_FILE = os.path.join(STATE_DIR, 'databases.json')
ADMIN_ROLE = 'cyberpanel_pgadmin'
ADMIN_DB = 'cyberpanel_postgres'
ADMINER_DIR = '/usr/local/CyberCP/public/postgres-adminer'
HBA_CANDIDATES = (
    '/var/lib/pgsql/data/pg_hba.conf',
    '/etc/postgresql/*/main/pg_hba.conf',
)


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


def _first_glob_existing(candidates):
    import glob
    for pattern in candidates:
        for item in glob.glob(pattern):
            if os.path.exists(item):
                return item
    return ''


def ensure_local_password_auth():
    hba = _first_glob_existing(HBA_CANDIDATES)
    if not hba:
        return False, 'pg_hba.conf not found.'
    try:
        with open(hba, 'r') as f:
            data = f.read()
        block = (
            "# cyberpanel-postgres-manager begin\n"
            "host    %s             %s             127.0.0.1/32            md5\n"
            "host    %s             %s             ::1/128                 md5\n"
            "host    all              %s             127.0.0.1/32            md5\n"
            "host    all              %s             ::1/128                 md5\n"
            "# cyberpanel-postgres-manager end\n\n"
        ) % (ADMIN_DB, ADMIN_ROLE, ADMIN_DB, ADMIN_ROLE, ADMIN_ROLE, ADMIN_ROLE)
        begin = '# cyberpanel-postgres-manager begin'
        end = '# cyberpanel-postgres-manager end'
        if begin in data and end in data:
            start = data.find(begin)
            finish = data.find(end, start) + len(end)
            if finish < len(data) and data[finish:finish + 1] == '\n':
                finish += 1
            data = data[:start] + block + data[finish:]
        else:
            marker = '# TYPE  DATABASE'
            idx = data.find(marker)
            if idx >= 0:
                line_end = data.find('\n', idx)
                data = data[:line_end + 1] + block + data[line_end + 1:]
            else:
                data += '\n' + block
        data = data.replace(
            'host    all             all             127.0.0.1/32            ident',
            'host    all             all             127.0.0.1/32            md5',
        )
        data = data.replace(
            'host    all             all             ::1/128                 ident',
            'host    all             all             ::1/128                 md5',
        )
        with open(hba, 'w') as f:
            f.write(data)
        service = detect_service()
        run_cmd(['systemctl', 'reload', service], timeout=20)
        return True, 'Local PostgreSQL password authentication is ready.'
    except (IOError, OSError) as exc:
        return False, str(exc)


def ensure_admin_credentials():
    ensure_local_password_auth()
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
        "CREATE ROLE %s WITH LOGIN SUPERUSER CREATEDB CREATEROLE PASSWORD '%s'; "
        "ELSE ALTER ROLE %s WITH LOGIN SUPERUSER CREATEDB CREATEROLE PASSWORD '%s'; "
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


def _ensure_state_dir():
    if not os.path.isdir(STATE_DIR):
        os.makedirs(STATE_DIR, 0o700)
    try:
        os.chmod(STATE_DIR, 0o700)
    except OSError:
        pass


def _load_records():
    _ensure_state_dir()
    try:
        with open(DATABASES_FILE, 'r') as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
    except (IOError, ValueError):
        pass
    return []


def _save_records(records):
    _ensure_state_dir()
    tmp_path = DATABASES_FILE + '.tmp'
    with open(tmp_path, 'w') as f:
        json.dump(records, f, indent=2, sort_keys=True)
        f.write('\n')
    os.chmod(tmp_path, 0o600)
    os.replace(tmp_path, DATABASES_FILE)


def _safe_suffix(value, field):
    value = (value or '').strip()
    if not re.match(r'^[A-Za-z0-9_]{1,32}$', value):
        raise ValueError('%s may only contain letters, numbers, and underscores.' % field)
    return value


def _domain_prefix(domain):
    label = (domain or '').split('.')[0].replace('-', '')
    label = re.sub(r'[^A-Za-z0-9_]', '', label).lower()
    if len(label) > 5:
        label = label[:4]
    return label or 'site'


def build_db_identifiers(domain, db_suffix, user_suffix):
    db_suffix = _safe_suffix(db_suffix, 'Database name')
    user_suffix = _safe_suffix(user_suffix, 'Username')
    prefix = _domain_prefix(domain)
    db_name = (prefix + '_' + db_suffix).lower()
    db_user = (prefix + '_' + user_suffix).lower()
    if len(db_name) > 63 or len(db_user) > 63:
        raise ValueError('Database name and username must be 63 characters or less after prefix.')
    return db_name, db_user


def quote_ident(value):
    if not re.match(r'^[A-Za-z_][A-Za-z0-9_]{0,62}$', value or ''):
        raise ValueError('Invalid PostgreSQL identifier.')
    return '"' + value.replace('"', '""') + '"'


def quote_literal(value):
    return "'" + (value or '').replace("'", "''") + "'"


def _psql(sql, database='postgres', timeout=30):
    return run_cmd(
        [psql_bin(), '-v', 'ON_ERROR_STOP=1', '-d', database, '-c', sql],
        timeout=timeout,
        user='postgres',
    )


def _scalar(sql, database='postgres'):
    ok, out = run_cmd(
        [psql_bin(), '-d', database, '-Atqc', sql],
        timeout=20,
        user='postgres',
    )
    return ok and out.strip() == '1'


def _database_exists(database):
    return _scalar("SELECT 1 FROM pg_database WHERE datname = %s" % quote_literal(database))


def _role_exists(username):
    return _scalar("SELECT 1 FROM pg_roles WHERE rolname = %s" % quote_literal(username))


def list_websites_for_user(user_id):
    from plogical.acl import ACLManager
    current_acl = ACLManager.loadedACL(user_id)
    return list(ACLManager.findAllSites(current_acl, user_id))


def _ensure_domain_allowed(user_id, domain):
    from loginSystem.models import Administrator
    from plogical.acl import ACLManager

    current_acl = ACLManager.loadedACL(user_id)
    admin = Administrator.objects.get(pk=user_id)
    if ACLManager.checkOwnership(domain, admin, current_acl) != 1:
        raise PermissionError('You do not own this website.')


def list_databases(user_id, domain=None):
    ensure_local_password_auth()
    allowed = set(list_websites_for_user(user_id))
    records = []
    for record in _load_records():
        if record.get('domain') not in allowed:
            continue
        if domain and record.get('domain') != domain:
            continue
        repair_database_record(record)
        public_record = dict(record)
        records.append(public_record)
    records.sort(key=lambda item: (item.get('domain', ''), item.get('database', '')))
    return records


def create_database(user_id, domain, db_suffix, user_suffix, password):
    if not password:
        raise ValueError('Password is required.')
    _ensure_domain_allowed(user_id, domain)
    ensure_admin_credentials()
    ensure_local_password_auth()
    db_name, db_user = build_db_identifiers(domain, db_suffix, user_suffix)
    records = _load_records()
    for record in records:
        if record.get('database') == db_name:
            raise ValueError('Database already exists in PostgreSQL Manager.')
        if record.get('username') == db_user:
            raise ValueError('Username already exists in PostgreSQL Manager.')

    ok, out = _psql(
        "CREATE ROLE %s WITH LOGIN PASSWORD %s;" % (quote_ident(db_user), quote_literal(password)),
        timeout=30,
    )
    if not ok:
        raise RuntimeError(out or 'PostgreSQL create failed.')
    ok, out = _psql(
        "CREATE DATABASE %s OWNER %s;" % (quote_ident(db_name), quote_ident(db_user)),
        timeout=45,
    )
    if not ok:
        _psql("DROP ROLE IF EXISTS %s;" % quote_ident(db_user), timeout=20)
        raise RuntimeError(out or 'PostgreSQL database create failed.')

    grants = (
        "GRANT ALL PRIVILEGES ON DATABASE %s TO %s; "
        "ALTER DATABASE %s OWNER TO %s;"
    ) % (quote_ident(db_name), quote_ident(db_user), quote_ident(db_name), quote_ident(db_user))
    ok, out = _psql(grants, database=db_name, timeout=30)
    if not ok:
        raise RuntimeError(out or 'PostgreSQL grants failed.')

    record = {
        'domain': domain,
        'database': db_name,
        'username': db_user,
        'password': password,
    }
    records.append(record)
    _save_records(records)
    return record


def change_database_password(user_id, database, username, password):
    if not password:
        raise ValueError('Password is required.')
    records = _load_records()
    for record in records:
        if record.get('database') == database and record.get('username') == username:
            _ensure_domain_allowed(user_id, record.get('domain'))
            repair_database_record(record)
            ok, out = _psql(
                "ALTER ROLE %s WITH PASSWORD %s;" % (quote_ident(username), quote_literal(password)),
                timeout=30,
            )
            if not ok:
                raise RuntimeError(out or 'Password change failed.')
            record['password'] = password
            _save_records(records)
            return record
    raise ValueError('Database record not found.')


def repair_database_record(record):
    database = record.get('database') or ''
    username = record.get('username') or ''
    password = record.get('password') or ''
    if not database or not username or not password:
        return False
    quote_ident(database)
    quote_ident(username)
    changed = False
    if not _role_exists(username):
        ok, out = _psql(
            "CREATE ROLE %s WITH LOGIN PASSWORD %s;" % (quote_ident(username), quote_literal(password)),
            timeout=30,
        )
        if not ok:
            raise RuntimeError(out or 'PostgreSQL role repair failed.')
        changed = True
    else:
        ok, out = _psql(
            "ALTER ROLE %s WITH LOGIN PASSWORD %s;" % (quote_ident(username), quote_literal(password)),
            timeout=30,
        )
        if not ok:
            raise RuntimeError(out or 'PostgreSQL role password repair failed.')
    if not _database_exists(database):
        ok, out = _psql(
            "CREATE DATABASE %s OWNER %s;" % (quote_ident(database), quote_ident(username)),
            timeout=45,
        )
        if not ok:
            raise RuntimeError(out or 'PostgreSQL database repair failed.')
        changed = True
    ok, out = _psql(
        "ALTER DATABASE %s OWNER TO %s; GRANT ALL PRIVILEGES ON DATABASE %s TO %s;" % (
            quote_ident(database),
            quote_ident(username),
            quote_ident(database),
            quote_ident(username),
        ),
        timeout=30,
    )
    if not ok:
        raise RuntimeError(out or 'PostgreSQL database ownership repair failed.')
    ok, out = _psql(
        "GRANT ALL ON SCHEMA public TO %s; "
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO %s; "
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO %s;" % (
            quote_ident(username),
            quote_ident(username),
            quote_ident(username),
        ),
        database=database,
        timeout=30,
    )
    if not ok:
        raise RuntimeError(out or 'PostgreSQL schema grant repair failed.')
    return changed


def delete_database(user_id, database, username):
    records = _load_records()
    next_records = []
    target = None
    for record in records:
        if record.get('database') == database and record.get('username') == username:
            target = record
        else:
            next_records.append(record)
    if not target:
        raise ValueError('Database record not found.')
    _ensure_domain_allowed(user_id, target.get('domain'))

    terminate_sql = (
        "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
        "WHERE datname = %s AND pid <> pg_backend_pid();"
    ) % quote_literal(database)
    _psql(terminate_sql, timeout=20)
    ok, out = _psql("DROP DATABASE IF EXISTS %s;" % quote_ident(database), timeout=45)
    if not ok:
        raise RuntimeError(out or 'Database deletion failed.')
    ok, out = _psql("DROP ROLE IF EXISTS %s;" % quote_ident(username), timeout=30)
    if not ok:
        raise RuntimeError(out or 'User deletion failed.')
    _save_records(next_records)
    return target
