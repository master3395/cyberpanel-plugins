# Plugin Development Guide

## Plugin Structure

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

## meta.xml Format

### Free Plugin Example

```xml
<?xml version="1.0" encoding="UTF-8"?>
<plugin>
    <name>Plugin Name</name>
    <type>Utility</type>
    <description>Plugin description</description>
    <version>1.0.0</version>
    <author>Your Name</author>
    <url>/plugins/pluginName/</url>
    <settings_url>/plugins/pluginName/settings/</settings_url>
</plugin>
```

### Paid Plugin Example

To create a paid plugin that requires Patreon subscription, add these fields:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<plugin>
    <name>Premium Plugin Name</name>
    <type>Utility</type>
    <description>Plugin description</description>
    <version>1.0.0</version>
    <author>Your Name</author>
    <url>/plugins/pluginName/</url>
    <settings_url>/plugins/pluginName/settings/</settings_url>
    <paid>true</paid>
    <patreon_tier>CyberPanel Paid Plugin</patreon_tier>
    <patreon_url>https://www.patreon.com/membership/27789984</patreon_url>
</plugin>
```

### Premium Plugin Fields

- `<paid>true</paid>` - Marks the plugin as paid
- `<patreon_tier>CyberPanel Paid Plugin</patreon_tier>` - The Patreon tier name users must subscribe to
- `<patreon_url>https://www.patreon.com/membership/27789984</patreon_url>` - Direct link to the Patreon membership page

### Visual Indicators

- Free plugins show a green "FREE" badge in Grid View, Table View, and Plugin Store
- Paid plugins show a yellow "PAID" badge in all views
- Paid plugins display a subscription warning with a "Subscribe on Patreon" button

## Requirements

- CyberPanel 2.5.5-dev or higher
- Python 3.6+
- Django (as used by CyberPanel)
- Compatible with CyberPanel plugin system

## CyberPanel 2.5.5-dev Features

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
