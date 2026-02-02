# WHMCS Integration

Documentation and links to the official CyberPanel WHMCS module. Integrate CyberPanel with WHMCS to sell and automate hosting services.

**Version:** 1.0.0  
**Type:** Integration  
**Pricing:** 🟢 **FREE**  
**Original Author:** jetchirag  
**Maintainer:** jesussuarz

## Description

This CyberPanel plugin provides documentation and quick links to the **official CyberPanel WHMCS module**. The WHMCS module is a separate PHP module that runs inside WHMCS (your billing software), not inside CyberPanel. It uses the CyberPanel API to provision and manage hosting accounts.

## Original Repository

- **Author:** jetchirag
- **Repository:** [github.com/jetchirag/cyberpanel-whmcs](https://github.com/jetchirag/cyberpanel-whmcs)

## Maintained Version

- **Maintainer:** jesussuarz
- **Repository:** [github.com/jesussuarz/cyberpanel-whmcs](https://github.com/jesussuarz/cyberpanel-whmcs)
- **Compatible with:** CyberPanel v2.5.5-dev

## WHMCS Module Features

- Create new website or user account
- Terminate website
- Suspend or unsuspend website
- Change hosting package
- Change user password
- Auto-login to CyberPanel (Admin or Customer)
- Store and display SSH credentials in WHMCS

## Installation (WHMCS Module)

1. SSH into your WHMCS server
2. Navigate to `path_to_whmcs/modules/servers`
3. Clone: `git clone https://github.com/jesussuarz/cyberpanel-whmcs.git cyberpanel`
4. Copy addon `modules/addons/cyberpanel_extra` to WHMCS addons directory
5. Activate CyberPanel Extra in WHMCS: System Settings → Addon Modules

## CyberPanel API Setup

Enable API Access in CyberPanel before using the WHMCS module:

1. Log in to CyberPanel
2. Go to **Users → API Access**
3. Select the admin user and **Enable API Access**
4. Or visit: `https://your-server:8090/users/apiAccess`

## URLs

- **Plugin URL:** `/plugins/whmcsIntegration/`

## Requirements

- CyberPanel v2.5.5-dev or higher (for API compatibility)
- WHMCS installation
