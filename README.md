# CyberPanel Plugins

A collection of plugins for CyberPanel web hosting control panel.

**Version:** 1.2.0  
**Author:** master3395  
**Compatible with:** CyberPanel 2.5.5-dev and higher

## Quick Links

- 📚 [Plugin Documentation](docs/plugins/)
- 📖 [Installation Guide](docs/guides/installation.md)
- 🛠️ [Development Guide](docs/guides/development.md)
- 💰 [Pricing Information](docs/guides/pricing.md)

## Available Plugins

| Plugin | Type | Pricing | Author | Description |
|--------|------|---------|--------|-------------|
| [Auto Snapshot for Contabo](contaboAutoSnapshot/) | Backup | 🟡 Paid | master3395 | Automated Contabo VPS snapshots |
| [CSP Manager](cspManager/) | Security | 🟢 Free | master3395 | Content Security Policy management |
| [Discord Authentication](discordAuth/) | Security | 🟢 Free | master3395 | Discord OAuth2 login for CyberPanel |
| [Discord Webhooks](docs/plugins/discordWebhooks.md) | Integration | 🟢 Free | master3395 | Send server notifications to Discord |
| [Email Marketing](emailMarketing/) | Email | 🟢 Free | usmannasir | Email marketing plugin for CyberPanel |
| [Example Plugin](examplePlugin/) | Utility | 🟢 Free | usmannasir | Example plugin demonstrating CyberPanel plugin structure |
| [Fail2ban Security Manager](docs/plugins/fail2ban.md) | Security | 🟢 Free | master3395 | Manage and monitor fail2ban settings |
| [Google Tag Manager](googleTagManager/) | Analytics | 🟢 Free | master3395 | Configure GTM container IDs per domain |
| [PayPal Premium Plugin Example](paypalPremiumPlugin/) | Utility | 🟡 Paid | master3395 | Example paid plugin with PayPal payment integration |
| [Memcache Manager](memcacheManager/) | Utility | 🟢 Free | master3395 | Manage Memcached/LSMCD: status, stats, flush, config |
| [Panel Access (Custom Domain)](panelAccess/) | Utility | 🟢 Free | master3395 | Configure custom domain(s) for accessing CyberPanel behind a reverse proxy |
| [PM2 Manager](docs/plugins/pm2Manager.md) | Development | 🟢 Free | master3395 | Manage PM2 Node.js process manager |
| [Premium Plugin Example](docs/plugins/premiumPlugin.md) | Utility | 🟡 Paid | master3395 | Example paid plugin with Patreon integration |
| [Redis Manager](redisManager/) | Utility | 🟢 Free | master3395 | Manage Redis: status, config, flush, load defaults, fix permissions |
| [SnappyMail Admin Password](snappymailAdmin/) | Email | 🟢 Free | master3395 | Set or change SnappyMail Admin panel username and password from CyberPanel |
| [Test Plugin](docs/plugins/testPlugin.md) | Utility | 🟢 Free | usmannasir | Basic test plugin for CyberPanel plugin system |

## Plugin Pricing

Plugins can be either **Free** or **Paid**:

- **Free Plugins**: Available to all users, no subscription required
- **Paid Plugins**: Require a Patreon subscription to a specific tier

See the [Pricing Guide](docs/guides/pricing.md) for more information.

## Installation

All plugins in this repository include `meta.xml` and required files so they work with **Install from store** in CyberPanel (Plugins → Installed → Store, or Install button fallback from grid).

Quick installation steps:

1. Download the plugin ZIP file
2. Upload via CyberPanel Plugin Manager
3. Install and activate

For detailed instructions, see the [Installation Guide](docs/guides/installation.md).

## Development

Want to create your own plugin? Check out the [Development Guide](docs/guides/development.md) for:

- Plugin structure
- meta.xml format
- Free and paid plugin examples
- Best practices

## Contributing

Contributions are welcome! Please ensure:

- Code follows CyberPanel standards
- Plugins are tested before submission
- Documentation is updated
- meta.xml is properly formatted

## Support

For issues and questions:

- Open an issue on [GitHub](https://github.com/master3395/cyberpanel-plugins/issues)
- Check plugin-specific documentation in [docs/plugins/](docs/plugins/)
- Review CyberPanel documentation

## License

These plugins are provided as-is for use with CyberPanel.

**MIT License**

---

**Author:** master3395  
_Last updated: 2026-02-02_  
_Compatible with CyberPanel 2.5.5-dev and higher_
