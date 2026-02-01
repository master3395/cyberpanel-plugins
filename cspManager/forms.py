# -*- coding: utf-8 -*-
"""
CSP Manager Forms
"""

from django import forms
from .models import CSPConfig


class CSPConfigForm(forms.ModelForm):
    """Form for CSP configuration"""
    
    class Meta:
        model = CSPConfig
        fields = [
            'csp_enabled',
            'apply_to_plugins',
            'apply_to_core',
            'allow_google_analytics',
            'allow_google_tag_manager',
            'allow_discord_auth',
            'allow_angularjs',
            'allow_jquery',
            'allow_cdn_resources',
            'permissive_plugin_csp',
        ]
        widgets = {
            'csp_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'apply_to_plugins': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'apply_to_core': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'allow_google_analytics': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'allow_google_tag_manager': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'allow_discord_auth': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'allow_angularjs': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'allow_jquery': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'allow_cdn_resources': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'permissive_plugin_csp': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
