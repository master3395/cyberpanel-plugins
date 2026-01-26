# Changelog - Fail2ban Security Manager

All notable changes to this plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] - 2026-01-26

### Fixed
- **JavaScript Function Scope Issues**: Fixed `Uncaught ReferenceError` for missing functions:
  - `showAddWhitelistModal()` - Now defined at top of script block for global scope
  - `showAddBlacklistModal()` - Now defined at top of script block for global scope
  - `refreshBannedIPs()` - Now defined at top of script block for global scope
  - `refreshLogs()` - Now defined at top of script block for global scope
  - `refreshStatistics()` - Now defined at top of script block for global scope
- **Function Availability**: Moved all utility functions (`getCookie`, `showAlert`, `closeModal`, `refreshJails`) to the top of the script block to ensure they're available immediately when the page loads, before any onclick handlers are called
- **Error Handling**: Added proper null checks and error logging in modal and refresh functions

### Changed
- **Code Organization**: Reorganized JavaScript code structure to define utility functions first, ensuring proper function hoisting and global scope availability
- **Function Definitions**: All onclick handler functions are now defined in global scope at the top of the script block

### Technical Details
- Functions were previously defined later in the script, causing `ReferenceError` when buttons were clicked before full script execution
- All functions are now hoisted to the top of the script block (lines 1052-1138) for immediate availability
- Added defensive programming with element existence checks and console error logging

## [1.0.0] - 2026-01-25

### Added
- Initial release of Fail2ban Security Manager plugin
- Real-time fail2ban monitoring and management
- IP whitelist/blacklist management
- Jail configuration and control
- Mobile-friendly responsive UI
- Security statistics and analytics
- Automated threat detection
- Email notifications
- Log analysis and reporting
- Unified settings page with tabbed interface
- Comprehensive API endpoints for all operations
- Singleton pattern for settings management
- Database models for persistent IP management
