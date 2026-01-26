# -*- coding: utf-8 -*-
"""
Discord OAuth2 Handler
Handles Discord OAuth2 authentication flow
"""

import urllib.request
import urllib.error
import urllib.parse
import json
import secrets
from django.conf import settings
from plogical.CyberCPLogFileWriter import CyberCPLogFileWriter as logging
from .config import get_config, get_redirect_uri


DISCORD_AUTHORIZE_URL = 'https://discord.com/api/oauth2/authorize'
DISCORD_TOKEN_URL = 'https://discord.com/api/oauth2/token'
DISCORD_USER_URL = 'https://discord.com/api/users/@me'


def generate_state():
    """Generate secure random state for OAuth flow"""
    return secrets.token_urlsafe(32)


def get_authorization_url(request, state=None):
    """
    Get Discord OAuth2 authorization URL
    Args:
        request: Django request object
        state: Optional state parameter (generated if not provided)
    Returns:
        str: Authorization URL or None if config invalid
    """
    config = get_config()
    
    if not config.get('client_id'):
        logging.writeToFile("Discord OAuth: Client ID not configured")
        return None
    
    if state is None:
        state = generate_state()
    
    redirect_uri = get_redirect_uri(request)
    scope = config.get('scope', 'identify email')
    
    params = {
        'client_id': config['client_id'],
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': scope,
        'state': state
    }
    
    url = f"{DISCORD_AUTHORIZE_URL}?{urllib.parse.urlencode(params)}"
    return url, state


def exchange_code_for_token(code, request):
    """
    Exchange authorization code for access token
    Args:
        code: Authorization code from Discord
        request: Django request object
    Returns:
        dict: Token data or None if failed
    """
    config = get_config()
    redirect_uri = get_redirect_uri(request)
    
    data = {
        'client_id': config['client_id'],
        'client_secret': config['client_secret'],
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': redirect_uri
    }
    
    try:
        req = urllib.request.Request(
            DISCORD_TOKEN_URL,
            data=urllib.parse.urlencode(data).encode('utf-8'),
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'User-Agent': 'CyberPanel-DiscordAuth/1.0'
            }
        )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            token_data = json.loads(response.read().decode('utf-8'))
            
            if 'access_token' in token_data:
                logging.writeToFile("Discord OAuth: Successfully exchanged code for token")
                return token_data
            else:
                logging.writeToFile(f"Discord OAuth: Token exchange failed - {token_data}")
                return None
                
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8') if e.fp else 'Unknown error'
        logging.writeToFile(f"Discord OAuth: HTTP error {e.code} - {error_body}")
        return None
    except Exception as e:
        logging.writeToFile(f"Discord OAuth: Error exchanging code - {str(e)}")
        return None


def get_discord_user(access_token):
    """
    Get Discord user information using access token
    Args:
        access_token: Discord OAuth2 access token
    Returns:
        dict: User data or None if failed
    """
    try:
        req = urllib.request.Request(
            DISCORD_USER_URL,
            headers={
                'Authorization': f'Bearer {access_token}',
                'User-Agent': 'CyberPanel-DiscordAuth/1.0'
            }
        )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            user_data = json.loads(response.read().decode('utf-8'))
            
            # Format user data consistently
            formatted_data = {
                'id': str(user_data.get('id', '')),
                'username': user_data.get('username', ''),
                'discriminator': user_data.get('discriminator', '0'),
                'email': user_data.get('email', ''),
                'avatar': user_data.get('avatar', ''),
                'verified': user_data.get('verified', False)
            }
            
            # Build avatar URL if avatar hash exists
            if formatted_data['avatar']:
                formatted_data['avatar_url'] = (
                    f"https://cdn.discordapp.com/avatars/"
                    f"{formatted_data['id']}/{formatted_data['avatar']}.png"
                )
            else:
                formatted_data['avatar_url'] = None
            
            logging.writeToFile(f"Discord OAuth: Retrieved user data for {formatted_data['username']}")
            return formatted_data
            
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8') if e.fp else 'Unknown error'
        logging.writeToFile(f"Discord OAuth: HTTP error {e.code} getting user - {error_body}")
        return None
    except Exception as e:
        logging.writeToFile(f"Discord OAuth: Error getting user data - {str(e)}")
        return None
