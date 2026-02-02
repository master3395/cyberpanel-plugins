# Changelog - CyberPanel Plugins

All notable changes to this repository will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
