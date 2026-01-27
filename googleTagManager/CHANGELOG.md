# Google Tag Manager Plugin Changelog

All notable changes to the Google Tag Manager plugin are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] - 2026-01-27

### Fixed
- **Settings page template error**: Fixed "Failed lookup for key [container_id] in '&lt;domain&gt;'" when opening plugin settings. The template used `gtm_settings|get_item:domain_info.domain.container_id`, which Django parsed as attribute lookup on the domain string (e.g. `'api.newstargeted.com'.container_id`) and raised an error.
- Settings page at `/plugins/googleTagManager/settings/` now loads correctly for all domains, including child domains.

### Changed
- **`templates/googleTagManager/settings.html`**: Introduced `{% with gtm_settings|get_item:domain_info.domain as domain_gtm %}` and use `domain_gtm`, `domain_gtm.container_id`, and `domain_gtm.enabled` instead of repeated `get_item` calls with chained attribute access.

### Technical Notes
- The fix resolves template resolution order: the filter argument `domain_info.domain.container_id` was previously evaluated as attribute lookup on the domain string before being passed to `get_item`.

---

## [1.0.0] - 2026-01-25

### Added
- Initial release of Google Tag Manager plugin
- Configure GTM container IDs per domain
- Enable/disable GTM per domain
- View and copy GTM code snippets (head and body)
- Integration with CyberPanel domain list

---

[1.0.1]: https://github.com/master3395/cyberpanel-plugins/compare/googleTagManager-v1.0.0...googleTagManager-v1.0.1
[1.0.0]: https://github.com/master3395/cyberpanel-plugins/releases/tag/googleTagManager-v1.0.0
