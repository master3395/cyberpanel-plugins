# Fix: `installPlugin() got an unexpected keyword argument 'zip_path'`

## Cause

The plugin store calls `pluginInstaller.installPlugin(name, zip_path=...)`. Older CyberPanel builds only define `installPlugin(pluginName)` and expect `pluginName.zip` in the current working directory.

## Fix (in CyberPanel core)

Update **`pluginHolder/views.py`** on the server (under `/usr/local/CyberCP/pluginHolder/views.py`) with the compatibility helper **`_install_plugin_compat`** and use it everywhere the store calls `installPlugin` with `zip_path`.

Reference implementation: [cyberpanel-repo `pluginHolder/views.py`](https://github.com) — search for `_install_plugin_compat` in your CyberPanel source tree or sync from a branch that includes this patch.

After editing:

```bash
systemctl restart lscpd
# or restart gunicorn for CyberPanel if applicable
```

Then retry **Install** for Limited phpMyAdmin from the store.

## Workaround (no core patch)

Upload the plugin ZIP via **Plugins → Install** (manual upload). Ensure the legacy `installPlugin` path can find the zip (same folder name as the plugin).
