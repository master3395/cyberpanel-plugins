# Limited phpMyAdmin

**Author:** master3395  
**Type:** Utility (free)  
**CyberPanel:** 2.5.5-dev and higher  

## Purpose

Create dedicated MySQL accounts that have privileges on **one database only**. You label each grant by **FTP user** or **CyberPanel user** for your own records. Contractors sign in to the panel’s phpMyAdmin (`/phpmyadmin/`) with the issued **MySQL username and password**—they do not need CyberPanel access.

## Features

- Domain/website filter and table of grants (similar workflow to FTP account management).
- **Disable**: revokes privileges on that database but **keeps** the grant row and MySQL user.
- **Enable**: restores `GRANT` on the configured database.
- **Delete**: drops the MySQL user and removes the grant row.
- **Password**: rotate MySQL password (shown once in a modal).
- **Database**: move the grant to another database on the same website (revoke old, grant new).

## Security notes

- Passwords are stored encrypted (Fernet) using a key file under `/home/cyberpanel/limitedPhpmyAdmin_fernet.key` (restrict permissions on the server).
- All API actions enforce CyberPanel ACL ownership for the selected website.
- Do not share credentials over insecure channels.

## Installation

Install from the CyberPanel plugin store or upload the plugin ZIP. With `enable_migrations` present, the installer runs migrations for the plugin app.

## Uninstall

Before removing the plugin, consider deleting grants from the UI so MySQL users are dropped. Orphan MySQL users named `cpma_*` can be removed manually in MariaDB if needed.
