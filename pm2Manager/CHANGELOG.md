# PM2 Manager Plugin Changelog

All notable changes to the PM2 Manager plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-01-27

### Added
- **Memory Limit Configuration**: Added ability to set memory limit for PM2 applications (e.g., "500M", "1G"). Applications will automatically restart when memory exceeds the specified limit.
- **Auto Restart Toggle**: Added option to enable/disable automatic restart on crash for PM2 applications.
- **Working Directory (CWD) Configuration**: Added ability to specify the current working directory for PM2 processes.
- **Interpreter Selection**: Added ability to specify custom interpreter for PM2 applications (e.g., "node", "python", "ruby").

### Changed
- Updated `add_pm2_app` function in `utils.py` to support new configuration options
- Enhanced Add App form in dashboard to include new configuration fields
- Updated JavaScript form handler to send new configuration parameters

### Technical Details
- Modified `utils.py`: Added `max_memory_restart`, `autorestart`, `cwd`, and `interpreter` parameters to `add_pm2_app` function
- Modified `views.py`: Updated `api_add_app` endpoint to accept and process new parameters
- Modified `dashboard.html`: Added form fields for memory limit, auto restart, working directory, and interpreter
- Modified `dashboard.js`: Updated form submission handler to include new fields

## [1.0.0] - 2026-01-19

### Added
- Initial release of PM2 Manager plugin
- Real-time monitoring with WebSocket support (fallback to polling)
- Process control (start, stop, restart, delete)
- Individual node details view
- Resource tracking (CPU and memory usage)
- Application management through web interface
- Cluster mode support
- Log viewing functionality
- Statistics dashboard

---

[1.1.0]: https://github.com/master3395/cyberpanel-plugins/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/master3395/cyberpanel-plugins/releases/tag/v1.0.0
