# Discord Auth Plugin - Installation Notes

## Automatic Integration

The plugin uses **middleware** to automatically inject the Discord login button into the login page. This means:

1. **No manual template modification needed** - The button appears automatically
2. **Works immediately after installation** - Just install and configure
3. **Non-invasive** - Doesn't modify CyberPanel core files

## How It Works

1. The `DiscordAuthMiddleware` intercepts responses to the login page
2. Checks if Discord auth is enabled via `/plugins/discordAuth/check/`
3. If enabled, injects the Discord login button HTML and JavaScript
4. The button appears below the regular login form

## Manual Integration (Alternative)

If the middleware doesn't work for some reason, you can manually add this to the login template:

```html
<!-- Add before </body> tag in login.html -->
{% load static %}
{% if discord_auth_enabled %}
<link rel="stylesheet" href="{% static 'discordAuth/css/discord-auth.css' %}">
<script src="{% static 'discordAuth/js/discord-login-inject.js' %}"></script>
{% endif %}
```

## Middleware Configuration

The middleware is automatically registered when the plugin is installed. To verify:

1. Check `settings.py` - `discordAuth` should be in `INSTALLED_APPS`
2. Check middleware - `discordAuth.middleware.DiscordAuthMiddleware` should be in `MIDDLEWARE`

## Troubleshooting

### Button Not Appearing

1. **Check if enabled**: Visit `/plugins/discordAuth/check/` - should return `{"enabled": true}`
2. **Check middleware**: Ensure middleware is in `MIDDLEWARE` setting
3. **Check static files**: Run `python manage.py collectstatic`
4. **Clear cache**: Clear browser cache and reload
5. **Check console**: Open browser console for JavaScript errors

### Middleware Not Working

If middleware injection doesn't work:

1. Check CyberPanel logs: `/home/cyberpanel/logs/error.log`
2. Verify plugin is installed correctly
3. Try manual integration method above
4. Check that `is_enabled()` returns `True`

## Testing

After installation:

1. Log out of CyberPanel
2. Visit login page
3. You should see "Login with Discord" button below the login form
4. Click it - should redirect to Discord
5. Authorize - should log you into CyberPanel

## Security Notes

- Middleware only injects on login page (`/` or pages with "login" in path)
- Only injects if Discord auth is enabled
- Checks are performed server-side
- No sensitive data in injected code
