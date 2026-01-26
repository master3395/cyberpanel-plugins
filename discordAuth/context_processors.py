# -*- coding: utf-8 -*-
"""
Discord Authentication Context Processors
Automatically injects Discord login script into login page
"""

from .utils.config import is_enabled


def discord_auth_context(request):
    """
    Context processor to add Discord auth information to templates
    This allows the login template to know if Discord auth is enabled
    """
    return {
        'discord_auth_enabled': is_enabled(),
        'discord_auth_url': '/plugins/discordAuth/login/',
    }
