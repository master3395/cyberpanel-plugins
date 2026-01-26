# -*- coding: utf-8 -*-
"""
Discord Authentication Configuration Manager
Handles secure storage and retrieval of Discord OAuth2 credentials
"""

import os
import json
from django.conf import settings
from plogical.CyberCPLogFileWriter import CyberCPLogFileWriter as logging


CONFIG_FILE = '/usr/local/CyberCP/discordAuth/config.json'
CONFIG_DIR = '/usr/local/CyberCP/discordAuth'


def ensure_config_dir():
    """Ensure config directory exists with proper permissions"""
    try:
        if not os.path.exists(CONFIG_DIR):
            os.makedirs(CONFIG_DIR, mode=0o700)
        return True
    except Exception as e:
        logging.writeToFile(f"Error creating config directory: {str(e)}")
        return False


def get_config():
    """
    Get Discord OAuth2 configuration from file
    Returns dict with client_id, client_secret, redirect_uri, scope
    """
    ensure_config_dir()
    
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                return {
                    'client_id': config.get('client_id', ''),
                    'client_secret': config.get('client_secret', ''),
                    'redirect_uri': config.get('redirect_uri', ''),
                    'scope': config.get('scope', 'identify email'),
                    'enabled': config.get('enabled', False),
                    'auto_create_users': config.get('auto_create_users', False),
                    'default_acl': config.get('default_acl', 'user')
                }
    except Exception as e:
        logging.writeToFile(f"Error reading Discord config: {str(e)}")
    
    return {
        'client_id': '',
        'client_secret': '',
        'redirect_uri': '',
        'scope': 'identify email',
        'enabled': False,
        'auto_create_users': False,
        'default_acl': 'user'
    }


def save_config(config_data):
    """
    Save Discord OAuth2 configuration to file
    Args:
        config_data: dict with client_id, client_secret, redirect_uri, scope, enabled, etc.
    Returns:
        bool: True if successful, False otherwise
    """
    ensure_config_dir()
    
    try:
        # Validate required fields
        if not config_data.get('client_id') or not config_data.get('client_secret'):
            return False
        
        config = {
            'client_id': config_data.get('client_id', ''),
            'client_secret': config_data.get('client_secret', ''),
            'redirect_uri': config_data.get('redirect_uri', ''),
            'scope': config_data.get('scope', 'identify email'),
            'enabled': config_data.get('enabled', False),
            'auto_create_users': config_data.get('auto_create_users', False),
            'default_acl': config_data.get('default_acl', 'user')
        }
        
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        
        # Set secure permissions (owner read/write only)
        os.chmod(CONFIG_FILE, 0o600)
        
        logging.writeToFile("Discord OAuth2 configuration saved successfully")
        return True
        
    except Exception as e:
        logging.writeToFile(f"Error saving Discord config: {str(e)}")
        return False


def is_enabled():
    """Check if Discord authentication is enabled"""
    config = get_config()
    return config.get('enabled', False) and bool(config.get('client_id'))


def get_redirect_uri(request):
    """
    Get redirect URI for Discord OAuth callback
    Uses request to determine full URL
    """
    config = get_config()
    redirect_uri = config.get('redirect_uri', '')
    
    if redirect_uri:
        return redirect_uri
    
    # Auto-generate redirect URI if not set
    scheme = 'https' if request.is_secure() else 'http'
    host = request.get_host()
    return f"{scheme}://{host}/plugins/discordAuth/callback/"
