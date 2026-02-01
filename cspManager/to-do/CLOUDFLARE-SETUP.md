# Cloudflare CSP Configuration for CyberPanel

## Issue
When accessing CyberPanel via domain (`https://cyberpanel.newstargeted.com/`), Cloudflare Transform Rules may override the CSP header, causing login issues.

## Solution

### Option 1: Update Cloudflare Transform Rules (Recommended)

1. Go to Cloudflare Dashboard → **Rules** → **Transform Rules** → **Modify Response Header**
2. Find any rule that sets `Content-Security-Policy` header
3. Update it to use the CSP from the CSP Manager plugin:

```
default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://www.jsdelivr.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://code.jquery.com https://www.google-analytics.com https://www.googletagmanager.com https://static.cloudflareinsights.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://www.jsdelivr.com https://cdnjs.cloudflare.com https://maxcdn.bootstrapcdn.com https://cdn.jsdelivr.net; img-src 'self' data: https: https://cdn.discordapp.com; font-src 'self' 'unsafe-inline' https://www.jsdelivr.com https://fonts.googleapis.com https://fonts.gstatic.com https://cdnjs.cloudflare.com; connect-src 'self' https: wss: ws: https://discord.com https://discordapp.com https://cdn.discordapp.com https://www.google-analytics.com https://www.googletagmanager.com https://stats.g.doubleclick.net https://static.cloudflareinsights.com; frame-ancestors 'none'; base-uri 'self'; form-action 'self';
```

### Option 2: Remove CSP from Cloudflare Transform Rules

If you can't update the Transform Rule, remove it entirely and let the CSP Manager plugin handle CSP:

1. Go to Cloudflare Dashboard → **Rules** → **Transform Rules**
2. Find the rule that sets `Content-Security-Policy`
3. Delete or disable it
4. The CSP Manager plugin will set the CSP header from the server

### Option 3: Use Cloudflare Page Rules (Alternative)

Create a Page Rule for `cyberpanel.newstargeted.com/*`:
- **Setting**: Disable Security
- **Or**: Set custom CSP via Transform Rules (see Option 1)

## How CSP Manager Handles Cloudflare

The CSP Manager plugin:
1. Detects Cloudflare via `CF-RAY`, `CF-CONNECTING-IP`, or `Via` headers
2. Sets both `Content-Security-Policy` and `X-Content-Security-Policy` headers
3. Sets `X-CSP-Source` header for Cloudflare Transform Rules to read
4. Ensures login pages work with permissive CSP

## Testing

After updating Cloudflare settings:
1. Clear browser cache
2. Hard refresh (Ctrl+Shift+R)
3. Try logging in via domain: `https://cyberpanel.newstargeted.com/`
4. Check browser console for CSP violations
5. Verify Google Analytics/Tag Manager load correctly

## Current Status

- ✅ IP access works: `https://207.180.193.210:2087/`
- ❌ Domain access blocked: `https://cyberpanel.newstargeted.com/` (Cloudflare override)

## Next Steps

1. Check Cloudflare Transform Rules for CSP overrides
2. Update or remove the Transform Rule
3. Test login via domain
4. Verify Google code loads correctly
