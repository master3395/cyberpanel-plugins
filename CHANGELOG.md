# Changelog - CyberPanel Plugins

All notable changes to this repository will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2026-02-15] - Settings routes and resilience

### Changed
- **panelAccess** (1.0.0 → 1.0.1): Added `settings/` route so `/plugins/panelAccess/settings/` works in Plugin Store grid.
- **cspManager** (1.0.1 → 1.0.2): Settings view handles missing DB table gracefully; prompts user to run `migrate cspManager` instead of 500.
- **examplePlugin** (1.0.1 → 1.0.2): Template directory layout and compatibility with panel plugin URL routing; ensure template dirs are readable (755) when deployed.

### Fixed
- **emailMarketing**: Added `settings/` route (version already 1.0.2). All plugins with a settings page now expose `/plugins/<name>/settings/` for the store.

## [2026-02-02] - Redis Manager & Memcache Manager 1.1.0 (CyberPanel 2.5.5-dev)

### Added
- **Redis Manager** (1.0.0 → 1.1.0): Confirmations on all Actions (Start, Stop, Restart, Flush All) and Save Settings; Load Default button to restore Redis config defaults; Fix permissions button and API when config file is unreadable; auto-detect config path (Redis INFO, process, systemd, find); deploy script and fix-permissions script.
- **Memcache Manager** (1.0.0 → 1.1.0): Version bump for CyberPanel 2.5.5-dev compatibility.
- **README**: Added Redis Manager and Memcache Manager to Available Plugins table.

### Changed
- **Redis Manager**: Settings form and Load Default always visible (including when config path not yet set); editable config defaults passed to template for reset.

## [2026-02-02] - Repository v1.2.0

### Changed
- **Repository version**: 1.1.0 → 1.2.0
- **README**: Added contaboAutoSnapshot and cspManager to Available Plugins table

### Fixed
- **cspManager**: Migration creates `cspManager_cspconfig` table; run `python3 manage.py migrate cspManager` if missing

## [2026-02-02] - Unified verification for all premium plugins

### Changed (premiumPlugin, paypalPremiumPlugin)
- **premiumPlugin** (1.0.1 → 1.0.2): Unified verification - Plugin Grants, activation key, Patreon, PayPal, AES-256-CBC encryption. Same flow as contaboAutoSnapshot.
- **paypalPremiumPlugin** (1.0.1 → 1.0.2): Unified verification - Plugin Grants, activation key, Patreon, PayPal, AES-256-CBC encryption. Same flow as contaboAutoSnapshot.

## [2026-02-02] - contaboAutoSnapshot 1.0.2

### Changed (contaboAutoSnapshot)
- **contaboAutoSnapshot** (1.0.1 → 1.0.2): Contabo API x-request-id fix (UUID4), max snapshots from plan, unified settings form, API credentials save once, activation key persistence, optional AES-256-CBC encryption for verification API, Plugin Grants auto-unlock

## [2026-02-01] - New categories added

### Added
- **Monitoring** - Health checks, metrics, alerts
- **Integration** - Webhooks, Discord, third-party APIs
- **Email** - Email marketing, deliverability
- **Development** - Dev tools, PM2, staging
- **Analytics** - Stats, GTM, reporting

### Changed (category reassignments)
- **discordWebhooks** (1.0.1 → 1.0.2): Utility → Integration
- **emailMarketing** (1.0.1 → 1.0.2): Utility → Email
- **googleTagManager** (1.0.1 → 1.0.2): Utility → Analytics
- **pm2Manager** (1.1.0 → 1.1.1): Utility → Development

## [2026-02-01] - Category updates and Plugin removal

### Changed
- **Plugin categories**: Removed the generic "Plugin" category. Valid categories are now: **Utility**, **Security**, **Backup**, **Performance**.
- **emailMarketing** (1.0.0 → 1.0.1): Updated `<type>` from `plugin` to `Utility`.
- **examplePlugin** (1.0.0 → 1.0.1): Updated `<type>` from `plugin` to `Utility`.
- **fail2ban** (1.0.1 → 1.0.2): Normalized `<type>` from `security` to `Security`.

### Migration
Plugins using `<type>plugin</type>` or `<type>Plugin</type>` will no longer appear in the Plugin Store. Update your meta.xml to use one of: Utility, Security, Backup, or Performance.
