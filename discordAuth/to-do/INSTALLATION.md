# Discord Authentication Plugin - Installation Guide

## Prerequisites

1. CyberPanel 2.5.5 or higher installed
2. Admin access to CyberPanel
3. Discord Developer Account
4. Discord Application created

## Step 1: Create Discord Application

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application"
3. Give it a name (e.g., "CyberPanel Auth")
4. Click "Create"

## Step 2: Configure OAuth2

1. In your Discord application, go to "OAuth2" in the left sidebar
2. Under "Redirects", click "Add Redirect"
3. Add your callback URL:
   ```
   https://your-cyberpanel-domain.com/plugins/discordAuth/callback/
   ```
   Replace `your-cyberpanel-domain.com` with your actual CyberPanel domain
4. Copy your **Client ID** and **Client Secret** (click "Reset Secret" if needed)
5. Save these for later

## Step 3: Install Plugin

1. Log into CyberPanel as administrator
2. Navigate to **Plugins** → **Installed Plugins**
3. Click **Upload Plugin**
4. Select the `discordAuth` plugin ZIP file
5. Wait for upload to complete
6. Click **Install** next to "Discord Authentication"
7. Wait for installation to complete

## Step 4: Configure Plugin

1. Navigate to **Plugins** → **Discord Authentication** → **Settings**
2. Enter your Discord credentials:
   - **Client ID**: Paste your Discord Client ID
   - **Client Secret**: Paste your Discord Client Secret
   - **Redirect URI**: Leave blank for auto-detection, or enter manually
   - **Scope**: Default is "identify email" (usually fine)
3. Enable options:
   - ✅ **Enable Discord Authentication**: Check this box
   - ⬜ **Auto Create Users**: Check if you want new Discord users to automatically get CyberPanel accounts
4. If auto-create is enabled, set **Default ACL** (e.g., "user")
5. Click **Save Settings**

## Step 5: Test Login

1. Log out of CyberPanel
2. On the login page, you should see a "Login with Discord" button
3. Click it and authorize with Discord
4. You should be logged into CyberPanel

## Troubleshooting

### Button Not Showing

- Verify plugin is installed and enabled
- Check that "Enable Discord Authentication" is checked in settings
- Clear browser cache and reload
- Check browser console for JavaScript errors

### OAuth Errors

- Verify redirect URI in Discord Developer Portal matches exactly
- Check Client ID and Client Secret are correct
- Ensure HTTPS is properly configured
- Check CyberPanel logs: `/home/cyberpanel/logs/error.log`

### Account Not Found

- Enable "Auto Create Users" in settings, OR
- First create a CyberPanel account, then link Discord account

## Security Notes

- Client Secret should be kept secure
- Config file is stored at `/usr/local/CyberCP/discordAuth/config.json` with 600 permissions
- All OAuth flows use HTTPS
- State parameter prevents CSRF attacks
