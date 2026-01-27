# Discord Authentication Plugin Changelog

All notable changes to the Discord Authentication plugin are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] - 2026-01-27

### Fixed
- **Template error on settings page**: Fixed "Error: baseTemplate/baseTemplate.html" when opening plugin settings or main page. Templates now correctly extend `baseTemplate/index.html` (CyberPanel standard) instead of non-existent `baseTemplate/baseTemplate.html`.
- Settings page at `/plugins/discordAuth/settings/` and plugin index at `/plugins/discordAuth/` now load without errors.

### Changed
- `templates/discordAuth/settings.html`: `{% extends "baseTemplate/baseTemplate.html" %}` → `{% extends "baseTemplate/index.html" %}`
- `templates/discordAuth/index.html`: `{% extends "baseTemplate/baseTemplate.html" %}` → `{% extends "baseTemplate/index.html" %}`

### Technical Notes
- After installing or upgrading, restart LiteSpeed (`systemctl restart lshttpd`) or restart lswsgi workers so template changes are picked up.

---

## [1.0.0] - 2026-01-26

### Added
- Initial release of Discord Authentication plugin
- Discord OAuth2 login for CyberPanel
- Account linking and optional automatic user creation
- Plugin settings page for Client ID, Client Secret, redirect URI, and options
- Login template integration (Discord button on login page)

---

[1.0.1]: https://github.com/master3395/cyberpanel-plugins/compare/discordAuth-v1.0.0...discordAuth-v1.0.1
[1.0.0]: https://github.com/master3395/cyberpanel-plugins/releases/tag/discordAuth-v1.0.0
