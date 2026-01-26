# Discord Auth Plugin - Troubleshooting

## Plugin Not Showing in Installed Plugins

If the plugin doesn't appear in `/plugins/installed`:

### 1. Verify Plugin Location

The plugin must be in `/home/cyberpanel/plugins/discordAuth/`:

```bash
ls -la /home/cyberpanel/plugins/discordAuth/
# Should show all plugin files including meta.xml
```

### 2. Check meta.xml

Verify `meta.xml` exists and is valid:

```bash
cat /home/cyberpanel/plugins/discordAuth/meta.xml
```

### 3. Check Permissions

Ensure proper ownership and permissions:

```bash
chown -R cyberpanel:cyberpanel /home/cyberpanel/plugins/discordAuth
find /home/cyberpanel/plugins/discordAuth -type f -exec chmod 644 {} \;
find /home/cyberpanel/plugins/discordAuth -type d -exec chmod 755 {} \;
```

### 4. Refresh CyberPanel

Try refreshing the plugin list:

1. **Via Web Interface**: 
   - Go to Plugins → Installed Plugins
   - Click refresh or reload the page
   - Clear browser cache

2. **Via Service Restart**:
   ```bash
   systemctl restart lscpd
   # OR
   service lscpd restart
   ```

3. **Via Gunicorn Restart** (if using):
   ```bash
   systemctl restart gunicorn
   # OR
   service gunicorn restart
   ```

### 5. Check CyberPanel Logs

Check for errors:

```bash
tail -f /home/cyberpanel/logs/error.log
# OR
tail -f /var/log/cyberpanel/error.log
```

### 6. Manual Detection Test

Test if CyberPanel can read the plugin:

```bash
cd /usr/local/CyberCP
python3 manage.py shell
>>> import os
>>> plugin_path = '/home/cyberpanel/plugins/discordAuth'
>>> os.path.exists(plugin_path)
True
>>> os.path.exists(plugin_path + '/meta.xml')
True
```

### 7. Verify Plugin Structure

Ensure all required files exist:

```bash
ls -la /home/cyberpanel/plugins/discordAuth/
# Should show:
# - meta.xml (REQUIRED)
# - __init__.py
# - apps.py
# - views.py
# - urls.py
# - models.py
# - templates/
# - static/
```

## After Plugin Appears

Once the plugin appears in the list:

1. **Click "Install"** button
2. Wait for installation to complete
3. **Configure** Discord credentials in settings
4. **Test** the login flow

## Common Issues

### Issue: "Plugin source not found"

**Solution**: Ensure plugin is in `/home/cyberpanel/plugins/discordAuth/`

### Issue: "Plugin already installed"

**Solution**: Check if already installed at `/usr/local/CyberCP/discordAuth/`

### Issue: Installation fails

**Solution**: 
- Check logs: `/home/cyberpanel/logs/error.log`
- Verify permissions
- Check disk space
- Verify Python/Django versions

### Issue: Button not appearing after installation

**Solution**:
1. Check if Discord auth is enabled in settings
2. Verify login template was modified
3. Clear browser cache
4. Check browser console for errors

## Manual Installation (If Needed)

If automatic installation fails:

```bash
# 1. Copy plugin to CyberCP directory
cp -r /home/cyberpanel/plugins/discordAuth /usr/local/CyberCP/

# 2. Add to INSTALLED_APPS
# Edit /usr/local/CyberCP/CyberCP/settings.py
# Add 'discordAuth', after 'emailPremium',

# 3. Add URL routing
# Edit /usr/local/CyberCP/CyberCP/urls.py
# Add: path('plugins/discordAuth/', include('discordAuth.urls')),

# 4. Run migrations
cd /usr/local/CyberCP
python3 manage.py makemigrations discordAuth
python3 manage.py migrate discordAuth

# 5. Collect static files
python3 manage.py collectstatic --noinput

# 6. Restart services
systemctl restart lscpd
```

## Still Not Working?

1. Check CyberPanel version (must be 2.5.5+)
2. Verify Python version (must be 3.6+)
3. Check Django version (must be 2.2+)
4. Review all logs
5. Try manual installation steps above
