# PostgreSQL Manager

Author: KraoESPfan1n

Free CyberPanel plugin that installs PostgreSQL, creates a dedicated local admin role, and exposes Adminer at `/postgres-adminer/` with an automatic PostgreSQL login button from the plugin page.

## What It Installs

- `postgresql-server` and `postgresql-contrib`
- The matching LiteSpeed PHP PostgreSQL extension where available, for example `lsphp83-pgsql`
- Adminer under `/usr/local/CyberCP/public/postgres-adminer/`
- A dedicated PostgreSQL role named `cyberpanel_pgadmin`
- A default database named `cyberpanel_postgres`

PostgreSQL is kept bound to localhost by default.

## Installation

From the plugin directory:

```bash
bash install.sh
```

Then open:

- CyberPanel plugin page: `/plugins/postgresManager/`
- PostgreSQL web console: `/postgres-adminer/`

The generated password is stored on the server at:

```text
/usr/local/CyberCP/pluginState/postgresManager/cyberpanel_pgadmin_password
```

## Compatibility

The installer supports:

- AlmaLinux, Rocky Linux, CentOS, RHEL style systems with `dnf` or `yum`
- Debian and Ubuntu systems with `apt-get`
- CyberPanel installs with dynamic plugin routing
- Older CyberPanel plugin routing by adding an idempotent fallback route in `pluginHolder/urls.py`
