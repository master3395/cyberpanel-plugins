# Google Tag Manager Plugin for CyberPanel

**Author:** master3395  
**Version:** 1.0.0  
**License:** MIT

## Overview

The Google Tag Manager (GTM) plugin for CyberPanel makes it easy to add Google Tag Manager container IDs to your domains. Configure GTM for each domain and get ready-to-use code snippets to add to your websites.

## Features

- ✅ Configure GTM container ID per domain
- ✅ Enable/disable GTM for individual domains
- ✅ View and copy GTM code snippets (head and body)
- ✅ Support for main domains and child domains
- ✅ User-friendly web interface
- ✅ Secure API endpoints
- ✅ Automatic validation of GTM container IDs

## Installation

### Prerequisites

- CyberPanel installed and running
- Admin or user access to CyberPanel
- Python 3.6+ and Django 2.2+

### Installation Steps

1. **Upload Plugin**
   - Log into CyberPanel as administrator
   - Navigate to **Plugins** → **Installed Plugins**
   - Click **Upload Plugin** button
   - Select the `googleTagManager.zip` file
   - Click **Upload**

2. **Install Plugin**
   - After upload, the plugin will appear in the plugin list
   - Click **Install** button next to the plugin
   - Wait for installation to complete

3. **Verify Installation**
   - Plugin should appear in the installed plugins list
   - Status should show as "Installed" and "Enabled"
   - Navigate to **Plugins** → **Google Tag Manager** to access the plugin

## Usage

### Getting Your GTM Container ID

1. Go to [Google Tag Manager](https://tagmanager.google.com/)
2. Sign in with your Google account
3. Create a new container or select an existing one
4. Copy your container ID (format: `GTM-XXXXXXX`)

### Configuring GTM for a Domain

1. Navigate to **Plugins** → **Google Tag Manager** → **Settings**
2. Find your domain in the list
3. Enter your GTM container ID (e.g., `GTM-XXXXXXX`)
4. Enable/disable GTM for the domain using the toggle switch
5. Click **Save**

### Getting Code Snippets

1. After configuring GTM for a domain, click **View Code** button
2. Copy the code for `<head>` section
3. Copy the code for `<body>` section
4. Add these code snippets to your website's HTML files

### Adding GTM Code to Your Website

#### For Static HTML Files

1. Open your website's main HTML file (usually `index.html`)
2. Add the `<head>` code immediately after the opening `<head>` tag
3. Add the `<body>` code immediately after the opening `<body>` tag
4. Save the file

#### For PHP Files

1. Open your website's main PHP file (usually `index.php` or `header.php`)
2. Add the `<head>` code in the `<head>` section
3. Add the `<body>` code right after the opening `<body>` tag
4. Save the file

#### For WordPress

1. Go to **Appearance** → **Theme Editor**
2. Edit `header.php`
3. Add the `<head>` code in the `<head>` section
4. Add the `<body>` code right after the opening `<body>` tag
5. Save the file

#### For CMS Made Simple

1. Go to **Layouts** → **Templates**
2. Edit your template
3. Add the `<head>` code in the `<head>` section
4. Add the `<body>` code right after the opening `<body>` tag
5. Save the template

## API Endpoints

The plugin provides several API endpoints for programmatic access:

### Get Domains
```
GET /plugins/googleTagManager/api/domains/
```
Returns list of domains accessible by the current user with their GTM status.

### Save GTM Settings
```
POST /plugins/googleTagManager/api/save/
Content-Type: application/json

{
    "domain": "example.com",
    "container_id": "GTM-XXXXXXX"
}
```

### Delete GTM Settings
```
POST /plugins/googleTagManager/api/delete/
Content-Type: application/json

{
    "domain": "example.com"
}
```

### Get GTM Code
```
GET /plugins/googleTagManager/api/code/{domain}/
```
Returns GTM code snippets for the specified domain.

### Toggle GTM Status
```
POST /plugins/googleTagManager/api/toggle/
Content-Type: application/json

{
    "domain": "example.com",
    "enabled": true
}
```

## File Structure

```
googleTagManager/
├── __init__.py
├── apps.py
├── models.py
├── views.py
├── urls.py
├── utils.py
├── meta.xml
├── README.md
├── migrations/
│   └── __init__.py
├── templates/
│   └── googleTagManager/
│       ├── index.html
│       └── settings.html
├── templatetags/
│   ├── __init__.py
│   └── gtm_tags.py
└── static/
    └── googleTagManager/
        ├── css/
        └── js/
```

## Database Schema

The plugin creates a `google_tag_manager_settings` table with the following structure:

- `id`: Primary key
- `domain`: Domain name (unique)
- `gtm_container_id`: GTM container ID (format: GTM-XXXXXXX)
- `enabled`: Boolean flag for enable/disable
- `website`: Foreign key to CyberPanel Websites (optional)
- `created_at`: Timestamp
- `updated_at`: Timestamp

## Security

- All views require CyberPanel authentication
- Domain access is validated using ACLManager
- GTM container IDs are validated for correct format
- API endpoints use CSRF protection
- User can only access domains they have permission for

## Troubleshooting

### Plugin Not Appearing

- Check that plugin is installed: `/usr/local/CyberCP/googleTagManager/`
- Verify `INSTALLED_APPS` in `settings.py` includes `googleTagManager`
- Check CyberPanel logs: `/var/log/cyberpanel/error.log`

### GTM Code Not Working

- Verify GTM container ID is correct
- Check that code snippets are added to both `<head>` and `<body>` sections
- Ensure GTM is enabled for the domain in plugin settings
- Verify website is loading the GTM code (check page source)

### Domain Not Showing

- Ensure domain exists in CyberPanel
- Check user has access to the domain
- Verify domain is not suspended

## Support

For issues, questions, or contributions:
- GitHub: https://github.com/master3395/cyberpanel-plugins
- Check CyberPanel logs: `/var/log/cyberpanel/error.log`

## Changelog

### Version 1.0.0 (2026-01-26)
- Initial release
- Basic GTM configuration per domain
- Code snippet generation
- Enable/disable functionality
- API endpoints for programmatic access

## License

MIT License - see LICENSE file for details

## Author

**master3395**

---

**Note:** This plugin requires CyberPanel to be installed and running. Make sure you have proper backups before installing plugins.
