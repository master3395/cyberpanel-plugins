# Limited phpMyAdmin

**Author:** master3395  
**Type:** Utility (free)  
**Version:** 1.1.1  
**CyberPanel:** 2.5.5-dev and higher  

## Changelog

### 1.1.1

- **Docs**: Clarified uninstall when the panel cannot write `settings.py` / `urls.py` (permissions, `chgrp lscpd` / `chmod 664`, optional root CLI `pluginInstaller.py remove --pluginName limitedPhpmyAdmin`).
- **Compatibility note**: On cores that **auto-sync** `INSTALLED_APPS` from disk, the plugin may not appear as a static line in `settings.py`; uninstall still rewrites core files—ensure the panel user can write them or use CLI as root.

### 1.1.0

- **Copy phpMyAdmin link / Open phpMyAdmin**: one-time launch URLs (24 h, single-use) that POST into CyberPanel’s `phpmyadminsignin.php` sign-on flow.
- **Bootstrap 3 compatibility**: replaced unsupported `d-none` with `.lpma-hidden` so alerts and the grants table display correctly.
- **Fernet key ownership**: key file is written for the `cyberpanel` user (WSGI), fixing “Failed to save grant” when encrypting passwords.
- **Migrations**: `websiteFunctions` stub migration support for FK resolution; `PmaLaunchToken` model for launch links.
- **UI**: grants section heading, sessionStorage domain restore, safer JSON bootstrap for site list.

## Purpose

Create dedicated MySQL accounts that have privileges on **one database only**. You label each grant by **FTP user** or **CyberPanel user** for your own records. Contractors sign in to the panel’s phpMyAdmin (`/phpmyadmin/`) with the issued **MySQL username and password**—they do not need CyberPanel access.

## Features

- Domain/website filter and table of grants (similar workflow to FTP account management).
- **Disable**: revokes privileges on that database but **keeps** the grant row and MySQL user.
- **Enable**: restores `GRANT` on the configured database.
- **Delete**: drops the MySQL user and removes the grant row.
- **Password**: rotate MySQL password (shown once in a modal).
- **Database**: move the grant to another database on the same website (revoke old, grant new).
- **Copy phpMyAdmin link** / **Open phpMyAdmin**: generate a one-time URL for the end user (no CyberPanel login required to *use* the link; only admins can create links). Treat links like secrets (HTTPS, short lifetime).

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

## Troubleshooting: plugin page returns HTTP 404

A **404** on `/plugins/limitedPhpmyAdmin/` usually means Django did **not** register the plugin routes (the URL is not handled).

1. **Confirm files exist**

   ```bash
   test -f /usr/local/CyberCP/limitedPhpmyAdmin/meta.xml && echo OK || echo MISSING
   test -f /usr/local/CyberCP/limitedPhpmyAdmin/urls.py && echo OK || echo MISSING
   ```

2. **Confirm the app loads** (imports `cryptography`, models, migrations):

   ```bash
   cd /usr/local/CyberCP
   python3 -c "import limitedPhpmyAdmin.urls; print('ok')"
   ```

   If this fails, install **`python3-cryptography`** (or `pip install cryptography`) on the server.

3. **Check `settings.py` auto-sync** (CyberPanel 2.5.5+): plugins under `/usr/local/CyberCP/<name>/` with `meta.xml` + `urls.py` are appended to `INSTALLED_APPS` automatically. If your `settings.py` has no such block, add `'limitedPhpmyAdmin',` inside `INSTALLED_APPS` manually, or upgrade CyberPanel.

4. **Look for “Skipping plugin” in logs**

   ```bash
   grep -i limitedPhpmyAdmin /usr/local/CyberCP/logs/*.log 2>/dev/null | tail -20
   ```

5. **Run migrations** (after `enable_migrations`):

   ```bash
   cd /usr/local/CyberCP
   python3 manage.py migrate limitedPhpmyAdmin
   ```

6. **Restart the panel**

   ```bash
   systemctl restart lscpd
   ```

## Troubleshooting: Uninstall fails (Permission denied: settings.py, urls.py, or index.html)

Uninstall **reads and writes** these files:

- `/usr/local/CyberCP/CyberCP/settings.py`
- `/usr/local/CyberCP/CyberCP/urls.py`
- `/usr/local/CyberCP/baseTemplate/templates/baseTemplate/index.html` (sidebar link removal)

If any of them are **root:root** and the panel user **cannot read** (mode `600`) or **cannot write** (mode `644` without group write), you may see **`[Errno 13] Permission denied`** on that path.

**One-time fix (as root):**

```bash
chgrp lscpd \
  /usr/local/CyberCP/CyberCP/settings.py \
  /usr/local/CyberCP/CyberCP/urls.py \
  /usr/local/CyberCP/baseTemplate/templates/baseTemplate/index.html
chmod 664 \
  /usr/local/CyberCP/CyberCP/settings.py \
  /usr/local/CyberCP/CyberCP/urls.py \
  /usr/local/CyberCP/baseTemplate/templates/baseTemplate/index.html
```

**CyberPanel `pluginInstaller`** (current `v2.5.5-dev` branch) uses a **privileged read/write copy** when direct access fails; deploy the latest `pluginInstaller/pluginInstaller.py` from the [cyberpanel](https://github.com/master3395/cyberpanel) repo to `/usr/local/CyberCP/pluginInstaller/`, then `systemctl restart lscpd`.

**CLI uninstall (always runs as root):**

```bash
cd /usr/local/CyberCP && python3 pluginInstaller/pluginInstaller.py remove --pluginName limitedPhpmyAdmin
```
