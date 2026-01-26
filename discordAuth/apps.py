# -*- coding: utf-8 -*-
from django.apps import AppConfig


class DiscordAuthConfig(AppConfig):
    name = 'discordAuth'
    verbose_name = 'Discord Authentication'
    
    def ready(self):
        """Import signals when app is ready"""
        import discordAuth.signals
