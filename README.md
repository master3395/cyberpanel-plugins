# CyberPanel Plugins

A collection of plugins for CyberPanel web hosting control panel.

**Author:** master3395  
**Compatible with:** CyberPanel 2.5.5-dev and higher

## Plugin Pricing

Plugins in this repository can be either **Free** or **Paid**:

- **Free Plugins**: Available to all users, no subscription required
- **Paid Plugins**: Require Patreon subscription to "CyberPanel Paid Plugin" tier

All plugins display their pricing status with badges:
- 🟢 **FREE** - Green badge for free plugins
- 🟡 **PAID** - Yellow badge for paid plugins

Badges appear in:
- Grid View (next to version)
- Table View (next to version)
- CyberPanel Plugin Store (separate "Pricing" column)

## Plugin Pricing

Plugins can be either **Free** or **Paid**:

- **Free Plugins**: Available to all users, no subscription required
- **Paid Plugins**: Require a Patreon subscription to a specific tier to use

Paid plugins will display:
- A "Paid" badge (yellow) in Grid, Table, and Store views
- A subscription warning with a link to the Patreon membership page
- Installation is allowed, but functionality requires an active subscription

## Available Plugins

### 1. Test Plugin

A simple test plugin to demonstrate the CyberPanel plugin system functionality.

**Version:** 1.0.0  
**Type:** Utility  
**Description:** A basic plugin for testing CyberPanel plugin installation, management, and functionality.

**Features:**
- Basic plugin structure
- Settings page
- Plugin information API
- Clean URL routing

**Installation:**
1. Download the plugin ZIP file
2. Upload via CyberPanel Plugin Manager
3. Install and activate

**URL:** `/plugins/testPlugin/`  
**Settings URL:** `/plugins/testPlugin/settings/`

---

### 2. Discord Webhooks

Send server notifications (SSH logins, security warnings, server usage) to Discord via webhooks.

**Version:** 1.0.0  
**Type:** Utility  
**Description:** Monitor your server and receive real-time notifications in Discord channels for SSH logins, security events, and server resource usage.

**Features:**
- SSH login notifications
- Security warning notifications (fail2ban bans, firewall blocks, etc.)
- Server usage monitoring (CPU, memory, disk, network)
- Configurable thresholds and check intervals
- Multiple webhook support
- Beautiful Discord embeds with metrics
- Powered by newstargeted.com

**Installation:**
1. Download the plugin ZIP file
2. Upload via CyberPanel Plugin Manager
3. Install and activate
4. Configure webhook URLs in plugin settings
5. Enable desired notification types

**Configuration:**
- Add Discord webhook URLs from your Discord server
- Configure event types to monitor
- Set server usage thresholds and check intervals
- Enable/disable individual webhooks

**URL:** `/plugins/discordWebhooks/`  
**Settings URL:** `/plugins/discordWebhooks/settings/`

**Requirements:**
- Python `psutil` library (usually pre-installed)
- Discord webhook URLs

**Author:** master3395

---

### 3. Fail2ban Security Manager

Manage and monitor fail2ban security settings through CyberPanel.

**Version:** 1.0.0  
**Type:** Security  
**Description:** Comprehensive fail2ban management interface for CyberPanel with jail configuration, IP management, and monitoring.

**Features:**
- Jail management
- IP ban/unban functionality
- Real-time monitoring
- Configuration management
- Security event tracking

**Installation:**
1. Download the plugin ZIP file
2. Upload via CyberPanel Plugin Manager
3. Install and activate

**URL:** `/plugins/fail2ban/`  
**Settings URL:** `/plugins/fail2ban/settings/`

**Requirements:**
- fail2ban installed on the server
- Appropriate system permissions

**Author:** master3395

---

### 4. Premium Plugin Example

An example paid plugin demonstrating the premium plugin system with Patreon subscription integration.

**Version:** 1.0.0  
**Type:** Utility  
**Description:** An example paid plugin that requires Patreon subscription to "CyberPanel Paid Plugin" tier. Users can install it but cannot run it without subscription.

**Features:**

* Premium plugin example
* Patreon subscription integration
* Subscription verification
* Remote API verification for security
* Example of paid plugin structure

**Installation:**

1. Download the plugin ZIP file
2. Upload via CyberPanel Plugin Manager
3. Install and activate
4. Subscribe to "CyberPanel Paid Plugin" tier on Patreon to use

**URL:** `/plugins/premiumPlugin/`  
**Settings URL:** `/plugins/premiumPlugin/settings/`

**Requirements:**

* Patreon subscription to "CyberPanel Paid Plugin" tier
* Active internet connection for subscription verification

**Author:** master3395

**Pricing:** Paid - Requires Patreon subscription

---

## Plugin Installation Guide

### Prerequisites

- CyberPanel installed and running
- Admin access to CyberPanel
- Server with appropriate permissions

### Installation Steps

1. **Download Plugin**
   - Download the plugin ZIP file from the releases or source code

2. **Upload Plugin**
   - Log into CyberPanel as administrator
   - Navigate to **Plugins** → **Installed Plugins**
   - Click **Upload Plugin**
   - Select the plugin ZIP file
   - Click **Upload**

3. **Install Plugin**
   - After upload, the plugin will appear in the list
   - Click **Install** button next to the plugin
   - Wait for installation to complete

4. **Configure Plugin**
   - Click **Manage** or **Settings** button
   - Configure plugin settings as needed
   - Save changes

5. **Enable Plugin**
   - Plugin is automatically enabled after installation
   - You can disable/enable from the plugin list

### Manual Installation (Advanced)

If automatic installation fails, you can manually install:

```bash
# 1. Extract plugin to CyberPanel directory
unzip plugin-name.zip -d /usr/local/CyberCP/

# 2. Add to INSTALLED_APPS in settings.py
# Edit /usr/local/CyberCP/CyberCP/settings.py
# Add 'pluginName', to INSTALLED_APPS list

# 3. Add URL routing
# Edit /usr/local/CyberCP/CyberCP/urls.py
# Add: path('plugins/pluginName/', include('pluginName.urls')),

# 4. Run migrations (if plugin has models)
cd /usr/local/CyberCP
python3 manage.py makemigrations pluginName
python3 manage.py migrate pluginName

# 5. Collect static files
python3 manage.py collectstatic --noinput

# 6. Restart CyberPanel
systemctl restart lscpd
```

## Plugin Development

### Plugin Structure

```
pluginName/
├── __init__.py
├── models.py          # Database models (optional)
├── views.py           # View functions
├── urls.py            # URL routing
├── forms.py           # Forms (optional)
├── utils.py           # Utility functions (optional)
├── admin.py           # Admin interface (optional)
├── templates/         # HTML templates
│   └── pluginName/
│       └── settings.html
├── static/            # Static files (CSS, JS, images)
│   └── pluginName/
├── migrations/        # Database migrations
├── meta.xml           # Plugin metadata (required)
└── README.md          # Plugin documentation
```

### meta.xml Format

**Basic Plugin (Free):**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<cyberpanelPluginConfig>
    <name>Plugin Name</name>
    <type>Utility</type>
    <description>Plugin description</description>
    <version>1.0.0</version>
    <url>/plugins/pluginName/</url>
    <settings_url>/plugins/pluginName/settings/</settings_url>
</cyberpanelPluginConfig>
```

**Premium Plugin (Paid):**

To create a paid plugin that requires Patreon subscription, add these fields:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<cyberpanelPluginConfig>
    <name>Premium Plugin Name</name>
    <type>Utility</type>
    <description>Plugin description</description>
    <version>1.0.0</version>
    <url>/plugins/pluginName/</url>
    <settings_url>/plugins/pluginName/settings/</settings_url>
    <paid>true</paid>
    <patreon_tier>CyberPanel Paid Plugin</patreon_tier>
    <patreon_url>https://www.patreon.com/membership/27789984</patreon_url>
</cyberpanelPluginConfig>
```

**Premium Plugin Fields:**
- `<paid>true</paid>` - Marks the plugin as paid
- `<patreon_tier>CyberPanel Paid Plugin</patreon_tier>` - The Patreon tier name users must subscribe to
- `<patreon_url>https://www.patreon.com/membership/27789984</patreon_url>` - Direct link to the Patreon membership page

**Visual Indicators:**
- Free plugins show a green "FREE" badge in Grid View, Table View, and Plugin Store
- Paid plugins show a yellow "PAID" badge in all views
- Paid plugins display a subscription warning with a "Subscribe on Patreon" button

### Requirements

- CyberPanel 2.5.5-dev or higher
- Python 3.6+
- Django (as used by CyberPanel)
- Compatible with CyberPanel plugin system

### CyberPanel 2.5.5-dev Features

All plugins in this repository are compatible with CyberPanel 2.5.5-dev and support:
- Enhanced plugin management interface
- GitHub commit date tracking
- Plugin store with caching
- Modify Date column in plugin tables
- **Premium/Paid plugin support with Patreon integration**
- Free/Paid badges in all views (Grid, Table, Store)
- Subscription verification and access control

## Contributing

Contributions are welcome! Please ensure:

- Code follows CyberPanel standards
- Plugins are tested before submission
- Documentation is updated
- meta.xml is properly formatted

## License

These plugins are provided as-is for use with CyberPanel.

## Support

For issues and questions:
- Open an issue on GitHub
- Check plugin-specific documentation
- Review CyberPanel documentation

## Author

**master3395**

---

*Last updated: 2026-01-19*  
*Compatible with CyberPanel 2.5.5-dev*
