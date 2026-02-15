# SnappyMail Admin Password – CyberPanel Plugin (Free)

Change the SnappyMail Admin panel password from CyberPanel when you forgot the login for `https://your-panel:2087/snappymail/?admin`.

## Install

1. Copy this folder to CyberPanel’s plugin location:
   - **Installed:** `cp -r snappymailAdmin /usr/local/CyberCP/`
   - Or keep it in source: `/home/cyberpanel-plugins/snappymailAdmin` (see PluginHolder `PLUGIN_SOURCE_PATHS`).

2. **Register the app** (required – otherwise `/plugins/snappymailAdmin/` returns 404):
   - **Option A (recommended):** On the server run:
     ```bash
     sudo bash /usr/local/CyberCP/snappymailAdmin/install.sh
     ```
     This adds `snappymailAdmin` to `INSTALLED_APPS` and restarts the panel.
   - **Option B:** Edit `/usr/local/CyberCP/CyberCP/settings.py`, and in `INSTALLED_APPS` add `'snappymailAdmin',` (e.g. after `'emailPremium',` or `'pluginHolder',`). Then restart: `sudo systemctl restart lscpd`.

3. Open **Plugins** in CyberPanel and open **SnappyMail Admin Password**, or go to:
   `https://your-panel:2087/plugins/snappymailAdmin/`.

4. Enter a new password and confirm, then click **Set SnappyMail Admin Password**. Log in at `.../snappymail/?admin` with the new password.

### If you get 404 on /plugins/snappymailAdmin/

The plugin URL is only registered when `snappymailAdmin` is in Django’s `INSTALLED_APPS`. Run `sudo bash /usr/local/CyberCP/snappymailAdmin/install.sh` (or add the app to `settings.py` and restart lscpd).

### If SnappyMail shows “Permission denied” for the data folder

If you see: **“SnappyMail can not access the data folder /usr/local/lscp/cyberpanel/snappymail/data/”** when opening `/snappymail/` or the plugin page:

1. On the server run (as root):
   ```bash
   sudo bash /usr/local/CyberCP/snappymailAdmin/fix_snappymail_permissions.sh
   ```
2. Or re-run the plugin install (it now fixes permissions when SnappyMail is present):
   ```bash
   sudo bash /usr/local/CyberCP/snappymailAdmin/install.sh
   ```

This creates the data directory if missing and sets ownership to `lscpd:lscpd` and permissions to `775` so the web server (PHP) can read/write the folder.

## Requirements

- SnappyMail installed at `/usr/local/CyberCP/public/snappymail/` and data at `/usr/local/lscp/cyberpanel/snappymail/data/`.
- PHP (LiteSpeed lsphp83/lsphp82/lsphp81 or system php).

Author: master3395 · Free plugin.
