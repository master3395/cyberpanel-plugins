# -*- coding: utf-8 -*-
"""
CSP Manager Models
Stores CSP configuration settings
"""

from django.db import models


class CSPConfig(models.Model):
    """
    Singleton model for CSP Manager configuration
    Only one instance should exist
    """
    # Global settings
    csp_enabled = models.BooleanField(default=True, help_text="Enable/disable CSP globally")
    apply_to_plugins = models.BooleanField(default=True, help_text="Apply CSP to plugin routes")
    apply_to_core = models.BooleanField(default=True, help_text="Apply CSP to core CyberPanel pages")
    
    # Plugin-specific settings (stored as JSON in a text field)
    # Format: {"plugin_name": {"enabled": true/false, "opt_out": true/false}}
    plugin_settings = models.TextField(
        default='{}',
        help_text="JSON object storing per-plugin CSP settings"
    )
    
    # CSP directives
    allow_google_analytics = models.BooleanField(default=True, help_text="Allow Google Analytics")
    allow_google_tag_manager = models.BooleanField(default=True, help_text="Allow Google Tag Manager")
    allow_discord_auth = models.BooleanField(default=True, help_text="Allow Discord Auth resources")
    allow_angularjs = models.BooleanField(default=True, help_text="Allow AngularJS from code.angularjs.org")
    allow_jquery = models.BooleanField(default=True, help_text="Allow jQuery from code.jquery.com")
    allow_cdn_resources = models.BooleanField(default=True, help_text="Allow CDN resources (jsDelivr, Cloudflare, etc.)")
    
    # Permissive mode for plugins
    permissive_plugin_csp = models.BooleanField(
        default=True,
        help_text="Use permissive CSP for plugins (allows more resources)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "CSP Configuration"
        verbose_name_plural = "CSP Configurations"
    
    def __str__(self):
        return f"CSP Config (Enabled: {self.csp_enabled})"
    
    @classmethod
    def get_config(cls):
        """Get or create the singleton CSP configuration"""
        config, created = cls.objects.get_or_create(pk=1)
        return config
    
    def get_plugin_setting(self, plugin_name, default=None):
        """Get setting for a specific plugin"""
        import json
        try:
            settings = json.loads(self.plugin_settings or '{}')
            return settings.get(plugin_name, default)
        except (json.JSONDecodeError, AttributeError):
            return default
    
    def set_plugin_setting(self, plugin_name, setting_key, value):
        """Set a setting for a specific plugin"""
        import json
        try:
            settings = json.loads(self.plugin_settings or '{}')
            if plugin_name not in settings:
                settings[plugin_name] = {}
            settings[plugin_name][setting_key] = value
            self.plugin_settings = json.dumps(settings)
            self.save()
        except (json.JSONDecodeError, AttributeError):
            pass
