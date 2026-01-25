# Discord Webhooks

Send server notifications (SSH logins, security warnings, server usage) to Discord via webhooks.

**Version:** 1.0.0  
**Type:** Utility  
**Pricing:** 🟢 **FREE**  
**Author:** master3395

## Description

Monitor your server and receive real-time notifications in Discord channels for SSH logins, security events, and server resource usage.

## Features

- SSH login notifications
- Security warning notifications (fail2ban bans, firewall blocks, etc.)
- Server usage monitoring (CPU, memory, disk, network)
- Configurable thresholds and check intervals
- Multiple webhook support
- Beautiful Discord embeds with metrics
- Powered by newstargeted.com

## Installation

1. Download the plugin ZIP file
2. Upload via CyberPanel Plugin Manager
3. Install and activate
4. Configure webhook URLs in plugin settings
5. Enable desired notification types

## Configuration

- Add Discord webhook URLs from your Discord server
- Configure event types to monitor
- Set server usage thresholds and check intervals
- Enable/disable individual webhooks

## URLs

- **Main URL:** `/plugins/discordWebhooks/`
- **Settings URL:** `/plugins/discordWebhooks/settings/`

## Requirements

- Python `psutil` library (usually pre-installed)
- Discord webhook URLs
- CyberPanel 2.5.5-dev or higher
