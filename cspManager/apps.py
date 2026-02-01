# -*- coding: utf-8 -*-
from django.apps import AppConfig
from django.conf import settings
import sys


class CSPManagerConfig(AppConfig):
    name = 'cspManager'
    verbose_name = 'CSP Manager'
    
    def ready(self):
        """Register middleware dynamically when app is ready"""
        # Auto-register app in INSTALLED_APPS if not already there (plugin-based, no core modification)
        if 'cspManager' not in settings.INSTALLED_APPS:
            settings.INSTALLED_APPS.append('cspManager')
        
        # Register middleware dynamically
        middleware_class = 'cspManager.middleware.CSPManagerMiddleware'
        if middleware_class not in settings.MIDDLEWARE:
            # Insert after secMiddleware so our CSP overrides the core CSP
            try:
                sec_middleware_index = settings.MIDDLEWARE.index('CyberCP.secMiddleware.secMiddleware')
                settings.MIDDLEWARE.insert(sec_middleware_index + 1, middleware_class)
            except (ValueError, AttributeError):
                # Fallback: append to end if secMiddleware not found
                settings.MIDDLEWARE.append(middleware_class)
