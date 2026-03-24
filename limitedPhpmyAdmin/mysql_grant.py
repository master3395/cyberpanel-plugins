# -*- coding: utf-8 -*-
"""
MySQL operations for single-database grants. Uses mysqlUtilities.setupConnection and LOCALHOST.
"""
from plogical.mysqlUtilities import mysqlUtilities
import plogical.CyberCPLogFileWriter as logging


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


def provision_mysql_user(database_name, mysql_username, password):
    """
    CREATE USER (if needed) + GRANT ALL on single database only.
    """
    try:
        conn, _ = mysqlUtilities.setupConnection()
        if conn == 0:
            return False, 'Could not connect to MySQL.'
        mysqlUtilities.addUserToDB(database_name, mysql_username, password, 1)
        r2 = mysqlUtilities.addUserToDB(database_name, mysql_username, password, 0)
        if r2 == 0:
            return False, 'Failed to grant database privileges.'
        return True, None
    except Exception as msg:
        logging.CyberCPLogFileWriter.writeToFile('limitedPhpmyAdmin provision_mysql_user: %s' % str(msg))
        return False, str(msg)


def grant_database_only(database_name, mysql_username, password):
    """
    GRANT ALL on database (user must already exist). Used after disable.
    """
    try:
        r = mysqlUtilities.addUserToDB(database_name, mysql_username, password, 0)
        if r == 0:
            return False, 'Failed to grant privileges.'
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
