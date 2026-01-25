# Plugin Installation Guide

## Prerequisites

- CyberPanel installed and running
- Admin access to CyberPanel
- Server with appropriate permissions

## Installation Steps

### 1. Download Plugin

Download the plugin ZIP file from the releases or source code.

### 2. Upload Plugin

1. Log into CyberPanel as administrator
2. Navigate to **Plugins** → **Installed Plugins**
3. Click **Upload Plugin**
4. Select the plugin ZIP file
5. Click **Upload**

### 3. Install Plugin

1. After upload, the plugin will appear in the list
2. Click **Install** button next to the plugin
3. Wait for installation to complete

### 4. Configure Plugin

1. Click **Manage** or **Settings** button
2. Configure plugin settings as needed
3. Save changes

### 5. Enable Plugin

- Plugin is automatically enabled after installation
- You can disable/enable from the plugin list

## Manual Installation (Advanced)

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
