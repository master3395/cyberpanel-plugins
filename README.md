# CyberPanel Plugins

A collection of plugins for CyberPanel web hosting control panel.

**Author:** master3395  
**Compatible with:** CyberPanel 2.5.5-dev and higher

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
