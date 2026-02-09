# Manual Test: Go To dashboard (PM2 Manager style)

After deploying the Fail2ban Security Manager plugin with the "Go To dashboard" update, verify in CyberPanel:

## 1. Plugin card (Plugins list)

- Go to **Plugins** (or **Plugin Manager** / **Installed Plugins**).
- Find **Fail2ban Security Manager**.
- Confirm the card shows (in order):
  - **Go To dashboard** (primary blue button, tachometer icon) → `/plugins/fail2ban/`
  - **Settings** (secondary grey) → `/plugins/fail2ban/settings/`
  - **Changelog** (info blue) → `/plugins/fail2ban/changelog/`
  - Enable Plugin toggle.
- Click **Go To dashboard** → should open the main Fail2ban unified dashboard (overview/jails/banned IPs/etc.).
- Click **Settings** → should open the simple settings page (plugin info + "Go to Fail2ban Security Manager Dashboard" button).

## 2. Simple settings page

- Open `/plugins/fail2ban/settings/` (or use **Settings** on the plugin card).
- Confirm:
  - Plugin Information section (name, version, status).
  - **Go to Fail2ban Security Manager Dashboard** button → opens `/plugins/fail2ban/`.
  - **Advanced settings** link → opens `/plugins/fail2ban/?tab=settings`.

## 3. Dashboard and advanced settings

- From the simple settings page, click **Go to Fail2ban Security Manager Dashboard**.
- Confirm the full dashboard loads (tabs: Overview, Manage Jails, Banned IPs, etc.).
- Open **Advanced settings** (or go to `/plugins/fail2ban/?tab=settings`) and confirm the Settings tab content loads.

## 4. Unit tests (optional)

From the CyberPanel project root (where the plugin is installed and in `INSTALLED_APPS`):

```bash
python manage.py test fail2ban.tests.Fail2banPluginTestCase.test_plugin_card_contains_go_to_dashboard
python manage.py test fail2ban.tests.Fail2banPluginTestCase.test_settings_simple_view
```

Both tests should pass.
