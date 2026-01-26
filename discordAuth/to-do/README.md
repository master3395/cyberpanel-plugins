# Discord Authentication Plugin for CyberPanel

**Version:** 1.0.0  
**Author:** master3395  
**License:** MIT

## Description

Discord Authentication plugin enables CyberPanel users to log in using their Discord account via OAuth2. This provides a secure and convenient authentication method without requiring users to remember separate passwords.

## Features

- **OAuth2 Authentication**: Secure login via Discord's OAuth2 system
- **Account Linking**: Link Discord accounts to existing CyberPanel accounts
- **Auto User Creation**: Optionally create new CyberPanel accounts automatically for Discord users
- **Session Management**: Full integration with CyberPanel's session system
- **Secure Configuration**: OAuth credentials stored securely in config file
- **Admin Interface**: Easy configuration through CyberPanel plugin settings

## Requirements

- CyberPanel 2.5.5 or higher
- Python 3.6+
- Django 2.2+
- Active Discord Developer Application

## Installation

1. **Upload Plugin**
   - Navigate to CyberPanel → Plugins → Installed Plugins
   - Click "Upload Plugin"
   - Select the `discordAuth` plugin ZIP file
   - Wait for upload to complete

2. **Install Plugin**
   - Click "Install" next to the Discord Authentication plugin
   - Wait for installation to complete

3. **Configure Discord Application**
   - Go to [Discord Developer Portal](https://discord.com/developers/applications)
   - Create a new application or select an existing one
   - Navigate to "OAuth2" section
   - Add redirect URI: `https://your-cyberpanel-domain.com/plugins/discordAuth/callback/`
   - Copy your Client ID and Client Secret

4. **Configure Plugin**
   - Navigate to Plugins → Discord Authentication → Settings
   - Enter your Discord Client ID and Client Secret
   - Set redirect URI (or leave blank for auto-detection)
   - Configure OAuth scope (default: "identify email")
   - Enable "Enable Discord Authentication"
   - Optionally enable "Automatically create new CyberPanel accounts"
   - Set default ACL for auto-created users
   - Click "Save Settings"

## Usage

### For Users

1. On the CyberPanel login page, click "Login with Discord"
2. You'll be redirected to Discord to authorize the application
3. After authorization, you'll be logged into CyberPanel

### For Administrators

- **View Plugin**: Navigate to Plugins → Discord Authentication
- **Configure**: Go to Settings to configure OAuth credentials
- **View Linked Accounts**: See which Discord accounts are linked to CyberPanel accounts

## Configuration

### OAuth2 Settings

- **Client ID**: Your Discord application's Client ID
- **Client Secret**: Your Discord application's Client Secret (keep secure!)
- **Redirect URI**: OAuth2 callback URL (auto-detected if not set)
- **Scope**: OAuth2 scopes (default: "identify email")

### Plugin Settings

- **Enable Discord Authentication**: Enable/disable Discord login
- **Auto Create Users**: Automatically create CyberPanel accounts for new Discord users
- **Default ACL**: ACL name to assign to auto-created users (default: "user")

## Security

- OAuth credentials are stored securely in `/usr/local/CyberCP/discordAuth/config.json` with 600 permissions
- State parameter validation prevents CSRF attacks
- Secure session management integrated with CyberPanel
- All OAuth flows use HTTPS

## Troubleshooting

### Discord Login Button Not Showing

- Ensure Discord authentication is enabled in plugin settings
- Check browser console for JavaScript errors
- Verify plugin is installed and enabled

### "Account Not Found" Error

- Enable "Auto Create Users" in settings, OR
- Link your Discord account to an existing CyberPanel account first

### OAuth Callback Errors

- Verify redirect URI in Discord Developer Portal matches your CyberPanel domain
- Check that Client ID and Client Secret are correct
- Ensure HTTPS is properly configured

## Support

For issues, questions, or contributions, please visit:
- GitHub: https://github.com/master3395/cyberpanel-plugins

## License

MIT License - See LICENSE file for details
