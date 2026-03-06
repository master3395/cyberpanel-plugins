# Deploy Plugin Fixes to Live Server (84.247.184.182)

After pushing the plugin fixes to `master3395/cyberpanel-plugins` (main), deploy on the live server using one of the following.

## Option A: Upgrade from CyberPanel Plugin Store (recommended)

1. Log in to the panel: https://84.247.184.182:2087/
2. Go to **Plugins** → **Installed Plugins** (or Plugin Store).
3. For each plugin that had issues, click **Upgrade** (if available):
   - contaboAutoSnapshot
   - cspManager
   - discordWebhooks
   - fail2ban
   - googleTagManager
   - redisManager
   - snappymailAdmin

Upgrade re-downloads the plugin from GitHub and runs the installer, which will now run migrations (thanks to `enable_migrations`).

## Option B: Run migrations manually (if tables already missing)

If you cannot upgrade from the store and only need to fix “table does not exist”:

```bash
sudo -u lscpd bash -c 'cd /usr/local/CyberCP && python3 manage.py migrate contaboAutoSnapshot'
sudo -u lscpd bash -c 'cd /usr/local/CyberCP && python3 manage.py migrate cspManager'
sudo -u lscpd bash -c 'cd /usr/local/CyberCP && python3 manage.py migrate discordWebhooks'
sudo -u lscpd bash -c 'cd /usr/local/CyberCP && python3 manage.py migrate fail2ban'
sudo -u lscpd bash -c 'cd /usr/local/CyberCP && python3 manage.py migrate googleTagManager'
sudo systemctl restart lscpd
```

## What was fixed

- **enable_migrations** added so install/upgrade runs Django migrations for contaboAutoSnapshot, cspManager, fail2ban, googleTagManager (discordWebhooks already had it).
- **redisManager**: D-Bus/systemctl errors (e.g. “Failed to connect to bus”) show a friendly message and config detection skips systemd when D-Bus is unavailable.
- **snappymailAdmin**: Admin URL shows the real panel host (e.g. https://84.247.184.182:2087/snappymail/?admin) instead of “your-panel”.
- **Defensive migrate**: cspManager, discordWebhooks, googleTagManager settings views try to run migrations once if the table is missing, then retry loading config.

## Verify

- https://84.247.184.182:2087/plugins/contaboAutoSnapshot/settings/
- https://84.247.184.182:2087/plugins/cspManager/settings/
- https://84.247.184.182:2087/plugins/discordWebhooks/settings/
- https://84.247.184.182:2087/plugins/fail2ban/settings/
- https://84.247.184.182:2087/plugins/googleTagManager/settings/
- https://84.247.184.182:2087/plugins/redisManager/
- https://84.247.184.182:2087/plugins/snappymailAdmin/ (Admin URL should show server IP)
