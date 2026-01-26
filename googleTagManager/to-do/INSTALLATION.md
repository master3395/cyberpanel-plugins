# Google Tag Manager Plugin - Installation Guide

## Quick Start

1. **Package the Plugin**
   ```bash
   cd /home/cyberpanel-plugins/googleTagManager
   ./package.sh
   ```
   This creates `googleTagManager.zip` in the plugin directory.

2. **Install via CyberPanel UI**
   - Log into CyberPanel as administrator
   - Go to **Plugins** → **Installed Plugins**
   - Click **Upload Plugin**
   - Select `googleTagManager.zip`
   - Click **Install**

3. **Access the Plugin**
   - Navigate to **Plugins** → **Google Tag Manager**
   - Or go directly to: `/plugins/googleTagManager/`

## Manual Installation (Advanced)

If automatic installation fails:

```bash
# 1. Copy plugin to CyberPanel directory
cp -r /home/cyberpanel-plugins/googleTagManager /usr/local/CyberCP/

# 2. Add to INSTALLED_APPS
# Edit /usr/local/CyberCP/CyberCP/settings.py
# Add 'googleTagManager', to INSTALLED_APPS list

# 3. Add URL routing
# Edit /usr/local/CyberCP/CyberCP/urls.py
# Add before generic plugin route:
# path('plugins/googleTagManager/', include('googleTagManager.urls')),

# 4. Run migrations
cd /usr/local/CyberCP
python3 manage.py makemigrations googleTagManager
python3 manage.py migrate googleTagManager

# 5. Collect static files
python3 manage.py collectstatic --noinput

# 6. Set permissions
chown -R cyberpanel:cyberpanel /usr/local/CyberCP/googleTagManager/

# 7. Restart CyberPanel
systemctl restart lscpd
```

## Verification

After installation, verify:

1. Plugin appears in **Plugins** → **Installed Plugins**
2. Can access `/plugins/googleTagManager/`
3. Database table `google_tag_manager_settings` exists
4. No errors in `/var/log/cyberpanel/error.log`

## Troubleshooting

- **Plugin not appearing**: Check `INSTALLED_APPS` in `settings.py`
- **Database errors**: Run migrations manually
- **Permission errors**: Check file ownership and permissions
- **Template errors**: Verify template files exist in correct location
