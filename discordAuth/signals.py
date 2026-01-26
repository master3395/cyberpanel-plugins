# -*- coding: utf-8 -*-
"""
Discord Authentication Signals
Handles plugin installation and setup
"""

from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.conf import settings
from plogical.CyberCPLogFileWriter import CyberCPLogFileWriter as logging
import os


@receiver(post_migrate)
def setup_discord_auth(sender, **kwargs):
    """
    Setup Discord auth after migrations
    Creates config directory and ensures proper permissions
    Also installs login template integration
    """
    if sender.name == 'discordAuth':
        try:
            # Create config directory
            config_dir = '/usr/local/CyberCP/discordAuth'
            if not os.path.exists(config_dir):
                os.makedirs(config_dir, mode=0o700)
                logging.writeToFile("Created Discord auth config directory")
            
            # Install login template integration
            from .install import install_discord_auth_integration
            install_discord_auth_integration()
            
            logging.writeToFile("Discord auth plugin setup complete")
        except Exception as e:
            logging.writeToFile(f"Error setting up Discord auth: {str(e)}")
