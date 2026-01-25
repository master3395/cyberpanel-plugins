# Plugin Pricing Guide

## Overview

Plugins in this repository can be either **Free** or **Paid**:

- **Free Plugins**: Available to all users, no subscription required
- **Paid Plugins**: Require a Patreon subscription to a specific tier to use

## Visual Indicators

All plugins display their pricing status with badges:

- 🟢 **FREE** - Green badge for free plugins
- 🟡 **PAID** - Yellow badge for paid plugins

Badges appear in:
- Grid View (next to version)
- Table View (next to version)
- CyberPanel Plugin Store (separate "Pricing" column)

## Paid Plugin Features

Paid plugins will display:

- A "Paid" badge (yellow) in Grid, Table, and Store views
- A subscription warning with a link to the Patreon membership page
- Installation is allowed, but functionality requires an active subscription

## Creating a Paid Plugin

To create a paid plugin, add these fields to your `meta.xml`:

```xml
<paid>true</paid>
<patreon_tier>Your Tier Name</patreon_tier>
<patreon_url>https://www.patreon.com/membership/YOUR_MEMBERSHIP_ID</patreon_url>
```

See the [Development Guide](development.md#paid-plugin-example) for complete examples.

## Subscription Verification

Paid plugins use remote API verification to check Patreon subscription status. This ensures:

- Security: Patreon credentials are not exposed in plugin code
- Reliability: Centralized verification service
- Privacy: User subscription status is verified securely
