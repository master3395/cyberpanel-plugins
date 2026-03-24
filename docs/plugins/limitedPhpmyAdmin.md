# Limited phpMyAdmin

**Author:** master3395  
**Type:** Utility (free)  
**CyberPanel:** 2.5.5-dev and higher  

## Purpose

Create dedicated MySQL accounts that have privileges on **one database only**. You label each grant by **FTP user** or **CyberPanel user** for your own records. Contractors sign in to the panel’s phpMyAdmin (`/phpmyadmin/`) with the issued **MySQL username and password**—they do not need CyberPanel access.

## Features

- Domain/website filter and table of grants (similar workflow to FTP account management).
- **Disable**: revokes privileges on that database but **keeps** the grant row and MySQL user.
- **Enable**: restores `GRANT` on the configured database.
- **Delete**: drops the MySQL user and removes the grant row.
- **Password**: rotate MySQL password (shown once in a modal).
- **Database**: move the grant to another database on the same website (revoke old, grant new).

## Security notes

- Passwords are stored encrypted (Fernet) using a key file under `/home/cyberpanel/limitedPhpmyAdmin_fernet.key` (restrict permissions on the server).
- All API actions enforce CyberPanel ACL ownership for the selected website.
- Do not share credentials over insecure channels.

## Installation

Install from the CyberPanel plugin store or upload the plugin ZIP. With `enable_migrations` present, the installer runs migrations for the plugin app.

## Uninstall

Before removing the plugin, consider deleting grants from the UI so MySQL users are dropped. Orphan MySQL users named `cpma_*` can be removed manually in MariaDB if needed.

## Troubleshooting: `/plugins/limitedPhpmyAdmin/` returns HTTP 404

A **404** means the URL is not registered (or the reverse proxy is not handing the request to CyberPanel’s Django app). It is **not** a bug inside the plugin page itself.

### 1. Confirm the plugin is installed on **this** server

The grid and routes only apply to the machine you are browsing. Check over SSH:

```bash
test -f /usr/local/CyberCP/limitedPhpmyAdmin/meta.xml && echo OK || echo MISSING
test -f /usr/local/CyberCP/limitedPhpmyAdmin/urls.py && echo OK || echo MISSING
```

If `MISSING`, install again from **Plugins → Install** (ZIP must contain a top-level folder `limitedPhpmyAdmin/` with `meta.xml` and `urls.py` inside it—not a double-nested folder).

### 2. Confirm Django can import the plugin URLs

```bash
cd /usr/local/CyberCP
python3 -c "import limitedPhpmyAdmin.urls; print('import ok')"
```

If this prints a traceback, fix the error (missing dependency, typo, permissions), then restart the panel stack (see step 4).

### 3. Confirm `CyberCP/urls.py` includes the plugin (installer usually adds this)

```bash
grep -n limitedPhpmyAdmin /usr/local/CyberCP/CyberCP/urls.py
```

You should see a line like `path('plugins/limitedPhpmyAdmin/', include('limitedPhpmyAdmin.urls'))`. If it is missing, reinstall the plugin or add the same pattern other plugins use (before the generic `plugins/` line if your version requires it).

### 4. Restart services after install/upgrade

```bash
systemctl restart lscpd
# If your stack uses gunicorn for CyberPanel:
systemctl restart gunicorn.socket 2>/dev/null || true
```

### 5. URL and protocol

- Path is **case-sensitive**: `/plugins/limitedPhpmyAdmin/` (camelCase `P`).
- Use the same **scheme** your panel uses (`https://` on 2087 is typical; if the panel is HTTP-only, use `http://`).

### 6. Check CyberPanel logs

Inspect recent errors in CyberPanel’s log writer / `pluginHolder` messages if imports fail at startup (plugin skipped when `urls` cannot be loaded).
