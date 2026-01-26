# Discord Auth Plugin - Final Setup Instructions

## ✅ Plugin is Ready!

The Discord Authentication plugin is now **fully functional** and will work immediately after installation.

## What Happens on Installation

1. **Plugin Installation**: Standard CyberPanel plugin installation process
2. **Database Migrations**: Creates Discord account linking tables
3. **Config Directory**: Creates `/usr/local/CyberCP/discordAuth/` with proper permissions
4. **Login Template Integration**: **Automatically** modifies login template to include Discord button
5. **Static Files**: Collected via `collectstatic`

## Automatic Integration

The plugin **automatically** modifies the login template during installation via:

- **Signal Handler**: `signals.py` runs after migrations
- **Installation Script**: `install.py` modifies login template
- **No Manual Steps Required**: Everything happens automatically!

## Post-Installation Steps

After installing the plugin:

1. **Configure Discord Application**:
   - Go to [Discord Developer Portal](https://discord.com/developers/applications)
   - Create/select application
   - Add redirect URI: `https://your-domain.com/plugins/discordAuth/callback/`
   - Copy Client ID and Client Secret

2. **Configure Plugin**:
   - Go to Plugins → Discord Authentication → Settings
   - Enter Client ID and Client Secret
   - Enable "Enable Discord Authentication"
   - Save settings

3. **Test**:
   - Log out of CyberPanel
   - Visit login page
   - You should see "Login with Discord" button
   - Click it and test the flow

## Verification

To verify everything is working:

1. **Check Config Directory**:
   ```bash
   ls -la /usr/local/CyberCP/discordAuth/
   # Should show config.json (after configuration)
   ```

2. **Check Login Template**:
   ```bash
   grep -i "discord" /usr/local/CyberCP/loginSystem/templates/loginSystem/login.html
   # Should show Discord auth injection code
   ```

3. **Check Plugin Status**:
   - Visit: `/plugins/discordAuth/check/`
   - Should return: `{"enabled": true}` (after configuration)

## Troubleshooting

### Button Not Appearing

1. **Check Installation**: Verify plugin is installed and enabled
2. **Check Configuration**: Ensure Discord auth is enabled in settings
3. **Check Template**: Verify login template was modified (see above)
4. **Clear Cache**: Clear browser cache and reload
5. **Check Console**: Open browser console for JavaScript errors

### Template Not Modified

If the login template wasn't automatically modified:

1. **Manual Installation**:
   ```python
   cd /usr/local/CyberCP
   python3 manage.py shell
   >>> from discordAuth.install import install_discord_auth_integration
   >>> install_discord_auth_integration()
   ```

2. **Or Restart CyberPanel**:
   ```bash
   service gunicorn restart
   ```

## Uninstallation

To remove the plugin:

1. **Uninstall via CyberPanel**: Plugins → Installed Plugins → Uninstall
2. **Manual Cleanup** (if needed):
   ```python
   from discordAuth.install import uninstall_discord_auth_integration
   uninstall_discord_auth_integration()
   ```

## Files Modified

The plugin automatically modifies:
- `/usr/local/CyberCP/loginSystem/templates/loginSystem/login.html` - Adds Discord button injection script

## Files Created

- `/usr/local/CyberCP/discordAuth/config.json` - Configuration (after setup)
- Database tables: `discord_auth_accounts`, `discord_auth_settings`

## Security

- Config file has 600 permissions (owner read/write only)
- Template modification is safe and reversible
- All OAuth flows use HTTPS
- State parameter prevents CSRF

## Support

If you encounter issues:

1. Check CyberPanel logs: `/home/cyberpanel/logs/error.log`
2. Check plugin logs in CyberPanel interface
3. Verify all installation steps completed
4. Test Discord OAuth configuration separately
