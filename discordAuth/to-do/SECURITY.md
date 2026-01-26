# Discord Authentication Plugin - Security Documentation

## Security Features

### 1. Secure Configuration Storage

- OAuth credentials stored in `/usr/local/CyberCP/discordAuth/config.json`
- File permissions set to 600 (owner read/write only)
- Config directory permissions set to 700
- No credentials in code or templates

### 2. OAuth2 Security

- **State Parameter**: Random state generated for each OAuth request
- **State Validation**: State verified on callback to prevent CSRF attacks
- **HTTPS Required**: All OAuth flows use HTTPS
- **Secure Token Exchange**: Tokens exchanged server-side only

### 3. Session Security

- Integration with CyberPanel's secure session system
- Session expiry: 12 hours (43200 seconds)
- IP address tracking for security
- Session state cleared after successful login

### 4. Input Validation

- All user inputs sanitized
- Discord user data validated before use
- SQL injection prevention via Django ORM
- XSS prevention via Django template escaping

### 5. Error Handling

- Secure error logging (no sensitive data in logs)
- Generic error messages to users
- Detailed errors logged server-side only
- No credential leakage in error messages

## Security Best Practices

### For Administrators

1. **Keep Client Secret Secure**
   - Never share Client Secret
   - Rotate if compromised
   - Use environment-specific applications

2. **HTTPS Configuration**
   - Ensure CyberPanel uses HTTPS
   - Valid SSL certificate required
   - HSTS enabled (recommended)

3. **Access Control**
   - Only admins can configure plugin
   - Regular users can only link their accounts
   - Monitor linked accounts regularly

4. **Regular Updates**
   - Keep plugin updated
   - Monitor security advisories
   - Update Discord application settings as needed

### For Users

1. **Account Security**
   - Use strong Discord account security
   - Enable 2FA on Discord account
   - Monitor linked accounts

2. **Session Management**
   - Log out when done
   - Don't share sessions
   - Use secure networks

## Security Considerations

### OAuth2 Flow Security

The plugin implements the standard OAuth2 authorization code flow:

1. User clicks "Login with Discord"
2. Random state generated and stored in session
3. User redirected to Discord with state
4. User authorizes application
5. Discord redirects back with code and state
6. State verified (CSRF protection)
7. Code exchanged for token (server-side)
8. User data retrieved with token
9. User logged into CyberPanel

### Data Protection

- Discord user data stored only as needed
- Email addresses stored if provided by Discord
- Avatar URLs stored (not images themselves)
- No Discord passwords stored (OAuth2 only)

### Privacy

- Users must explicitly authorize Discord access
- Only requested scopes are used
- No data shared with third parties
- All data stored on CyberPanel server

## Reporting Security Issues

If you discover a security vulnerability:

1. **DO NOT** create a public issue
2. Email security details to: [Your Security Email]
3. Include:
   - Description of vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

## Security Checklist

- [ ] HTTPS enabled on CyberPanel
- [ ] Client Secret stored securely
- [ ] Redirect URI configured correctly
- [ ] State parameter validation working
- [ ] Session security configured
- [ ] Error logging configured
- [ ] Regular security updates applied
- [ ] Access control properly configured
