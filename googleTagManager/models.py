# -*- coding: utf-8 -*-
"""
Google Tag Manager Plugin Models
Stores GTM container IDs per domain
"""

from django.db import models
from django.core.validators import RegexValidator
from websiteFunctions.models import Websites, ChildDomains


class GTMSettings(models.Model):
    """
    Stores Google Tag Manager container ID for each domain
    """
    domain = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text="Domain name (e.g., example.com)"
    )
    gtm_container_id = models.CharField(
        max_length=20,
        validators=[
            RegexValidator(
                regex=r'^GTM-[A-Z0-9]+$',
                message='GTM container ID must be in format GTM-XXXXXXX'
            )
        ],
        help_text="Google Tag Manager container ID (e.g., GTM-XXXXXXX)"
    )
    enabled = models.BooleanField(
        default=True,
        help_text="Enable GTM for this domain"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Optional: Link to CyberPanel website object
    website = models.ForeignKey(
        Websites,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='gtm_settings',
        help_text="Linked CyberPanel website (optional)"
    )
    
    class Meta:
        db_table = 'google_tag_manager_settings'
        verbose_name = 'GTM Settings'
        verbose_name_plural = 'GTM Settings'
        ordering = ['domain']
        indexes = [
            models.Index(fields=['domain']),
            models.Index(fields=['enabled']),
        ]
    
    def __str__(self):
        status = "Enabled" if self.enabled else "Disabled"
        return f"{self.domain} - {self.gtm_container_id} ({status})"
    
    def clean(self):
        """Validate GTM container ID format"""
        from django.core.exceptions import ValidationError
        
        if not self.gtm_container_id.startswith('GTM-'):
            raise ValidationError({
                'gtm_container_id': 'GTM container ID must start with "GTM-"'
            })
        
        # Remove GTM- prefix for validation
        container_id = self.gtm_container_id.replace('GTM-', '')
        if not container_id or len(container_id) < 4:
            raise ValidationError({
                'gtm_container_id': 'GTM container ID must have at least 4 characters after "GTM-"'
            })
