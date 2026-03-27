# -*- coding: utf-8 -*-
"""
MySQL operations for single-database grants. Uses mysqlUtilities.setupConnection and LOCALHOST.
"""
from plogical.mysqlUtilities import mysqlUtilities
import plogical.CyberCPLogFileWriter as logging

ALL_PRIVILEGES_TOKEN = 'ALL'
SUPPORTED_PRIVILEGES = (
    'SELECT',
    'INSERT',
    'UPDATE',
    'DELETE',
    'CREATE',
    'ALTER',
    'INDEX',
    'DROP',
    'CREATE TEMPORARY TABLES',
    'LOCK TABLES',
)


def _backtick_db(db_name):
    return '`' + str(db_name).replace('`', '``') + '`'


def _flush_close(conn, cur):
    try:
        cur.execute('FLUSH PRIVILEGES')
    except Exception as msg:
        logging.CyberCPLogFileWriter.writeToFile('limitedPhpmyAdmin flush: %s' % str(msg))
    try:
        conn.close()
    except Exception:
        pass


def normalize_privileges(privileges):
    """
    Normalize user-provided privilege input.
    Returns either ['ALL'] or a de-duplicated list of SUPPORTED_PRIVILEGES.
    """
    if privileges is None:
        return [ALL_PRIVILEGES_TOKEN]

    if isinstance(privileges, str):
        raw_items = [p.strip() for p in privileges.split(',')]
    elif isinstance(privileges, (list, tuple)):
        raw_items = [str(p or '').strip() for p in privileges]
    else:
        raw_items = []

    cleaned = []
    seen = set()
    for item in raw_items:
        if not item:
            continue
        upper = item.upper()
        if upper == ALL_PRIVILEGES_TOKEN:
            return [ALL_PRIVILEGES_TOKEN]
        for allowed in SUPPORTED_PRIVILEGES:
            if upper == allowed.upper() and allowed not in seen:
                cleaned.append(allowed)
                seen.add(allowed)
                break

    if not cleaned:
        return [ALL_PRIVILEGES_TOKEN]
    return cleaned


def serialize_privileges(privileges):
    normalized = normalize_privileges(privileges)
    return ALL_PRIVILEGES_TOKEN if normalized == [ALL_PRIVILEGES_TOKEN] else ','.join(normalized)


def deserialize_privileges(serialized_value):
    return normalize_privileges(serialized_value)


def _set_database_privileges(database_name, mysql_username, privileges):
    conn, cur = mysqlUtilities.setupConnection()
    if conn == 0:
        return False, 'Could not connect to MySQL.'
    try:
        host = mysqlUtilities.LOCALHOST
        u = mysqlUtilities._sanitize_mysql_identifier(mysql_username)
        h = mysqlUtilities._sanitize_mysql_identifier(host)
        db_bt = _backtick_db(database_name)

        # Start from a clean privilege set for this database.
        cur.execute("REVOKE ALL PRIVILEGES ON %s.* FROM '%s'@'%s'" % (db_bt, u, h))
        normalized = normalize_privileges(privileges)
        if normalized == [ALL_PRIVILEGES_TOKEN]:
            cur.execute("GRANT ALL PRIVILEGES ON %s.* TO '%s'@'%s'" % (db_bt, u, h))
        else:
            grant_clause = ', '.join(normalized)
            cur.execute("GRANT %s ON %s.* TO '%s'@'%s'" % (grant_clause, db_bt, u, h))

        _flush_close(conn, cur)
        return True, None
    except Exception as msg:
        logging.CyberCPLogFileWriter.writeToFile('limitedPhpmyAdmin set privileges: %s' % str(msg))
        try:
            conn.close()
        except Exception:
            pass
        return False, str(msg)


def provision_mysql_user(database_name, mysql_username, password, privileges=None):
    """
    CREATE USER (if needed) + GRANT privileges on single database only.
    """
    try:
        conn, _ = mysqlUtilities.setupConnection()
        if conn == 0:
            return False, 'Could not connect to MySQL.'
        mysqlUtilities.addUserToDB(database_name, mysql_username, password, 1)
        r2 = mysqlUtilities.addUserToDB(database_name, mysql_username, password, 0)
        if r2 == 0:
            return False, 'Failed to grant database privileges.'
        normalized = normalize_privileges(privileges)
        if normalized != [ALL_PRIVILEGES_TOKEN]:
            ok, err = _set_database_privileges(database_name, mysql_username, normalized)
            if not ok:
                return False, err or 'Failed to set custom privileges.'
        return True, None
    except Exception as msg:
        logging.CyberCPLogFileWriter.writeToFile('limitedPhpmyAdmin provision_mysql_user: %s' % str(msg))
        return False, str(msg)


def grant_database_only(database_name, mysql_username, password, privileges=None):
    """
    GRANT on database (user must already exist). Used after disable.
    """
    try:
        normalized = normalize_privileges(privileges)
        if normalized == [ALL_PRIVILEGES_TOKEN]:
            r = mysqlUtilities.addUserToDB(database_name, mysql_username, password, 0)
            if r == 0:
                return False, 'Failed to grant privileges.'
        else:
            ok, err = _set_database_privileges(database_name, mysql_username, normalized)
            if not ok:
                return False, err or 'Failed to set custom privileges.'
        return True, None
    except Exception as msg:
        logging.CyberCPLogFileWriter.writeToFile('limitedPhpmyAdmin grant_database_only: %s' % str(msg))
        return False, str(msg)


def revoke_database_privileges(database_name, mysql_username):
    """
    REVOKE ALL on database.* — keeps MySQL user account for soft-disable.
    """
    conn, cur = mysqlUtilities.setupConnection()
    if conn == 0:
        return False, 'Could not connect to MySQL.'
    try:
        host = mysqlUtilities.LOCALHOST
        u = mysqlUtilities._sanitize_mysql_identifier(mysql_username)
        h = mysqlUtilities._sanitize_mysql_identifier(host)
        db_bt = _backtick_db(database_name)
        sql = 'REVOKE ALL PRIVILEGES ON %s.* FROM \'%s\'@\'%s\'' % (db_bt, u, h)
        cur.execute(sql)
        _flush_close(conn, cur)
        return True, None
    except Exception as msg:
        logging.CyberCPLogFileWriter.writeToFile('limitedPhpmyAdmin revoke: %s' % str(msg))
        try:
            conn.close()
        except Exception:
            pass
        return False, str(msg)


def drop_mysql_user(mysql_username):
    """
    DROP USER for this host. Idempotent where supported.
    """
    conn, cur = mysqlUtilities.setupConnection()
    if conn == 0:
        return False, 'Could not connect to MySQL.'
    try:
        host = mysqlUtilities.LOCALHOST
        u = mysqlUtilities._sanitize_mysql_identifier(mysql_username)
        h = mysqlUtilities._sanitize_mysql_identifier(host)
        # MariaDB / MySQL 5.7+ support IF EXISTS
        cur.execute("DROP USER IF EXISTS '%s'@'%s'" % (u, h))
        _flush_close(conn, cur)
        return True, None
    except Exception as msg:
        logging.CyberCPLogFileWriter.writeToFile('limitedPhpmyAdmin drop_mysql_user: %s' % str(msg))
        try:
            conn.close()
        except Exception:
            pass
        return False, str(msg)


def change_mysql_password(mysql_username, new_password):
    ok = mysqlUtilities.changePassword(mysql_username, new_password, encrypt=None, host=None)
    if ok == 1:
        return True, None
    return False, 'Failed to change MySQL password.'


def change_database_for_user(old_db, new_db, mysql_username, password_plain):
    """
    REVOKE on old DB, GRANT on new DB (user unchanged).
    """
    ok, err = revoke_database_privileges(old_db, mysql_username)
    if not ok:
        return False, err or 'Revoke failed'
    return grant_database_only(new_db, mysql_username, password_plain)
