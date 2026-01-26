# -*- coding: utf-8 -*-
"""
Discord Authentication Models
Stores Discord account linking information
"""

from django.db import models
from loginSystem.models import Administrator


class DiscordAccount(models.Model):
    """
    Links Discord accounts to CyberPanel administrators
    """
    admin = models.OneToOneField(
        Administrator,
        on_delete=models.CASCADE,
        related_name='discord_account',
        verbose_name='Administrator'
    )
    discord_id = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        verbose_name='Discord User ID'
    )
    discord_username = models.CharField(
        max_length=100,
        verbose_name='Discord Username'
    )
    discord_discriminator = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        verbose_name='Discord Discriminator'
    )
    discord_email = models.EmailField(
        blank=True,
        null=True,
        verbose_name='Discord Email'
    )
    discord_avatar = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name='Discord Avatar URL'
    )
    linked_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Linked At'
    )
    last_used = models.DateTimeField(
        auto_now=True,
        verbose_name='Last Used'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Is Active'
    )

    class Meta:
        verbose_name = 'Discord Account'
        verbose_name_plural = 'Discord Accounts'
        db_table = 'discord_auth_accounts'

    def __str__(self):
        return f"{self.discord_username}#{self.discord_discriminator} ({self.admin.userName})"


class DiscordAuthSettings(models.Model):
    """
    Stores Discord OAuth2 configuration
    """
    client_id = models.CharField(
        max_length=100,
        verbose_name='Discord Client ID'
    )
    client_secret = models.CharField(
        max_length=200,
        verbose_name='Discord Client Secret'
    )
    redirect_uri = models.URLField(
        max_length=500,
        verbose_name='Redirect URI'
    )
    scope = models.CharField(
        max_length=200,
        default='identify email',
        verbose_name='OAuth Scope'
    )
    enabled = models.BooleanField(
        default=False,
        verbose_name='Enable Discord Auth'
    )
    auto_create_users = models.BooleanField(
        default=False,
        verbose_name='Auto Create Users'
    )
    default_acl = models.CharField(
        max_length=50,
        default='user',
        blank=True,
        verbose_name='Default ACL for New Users'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )

    class Meta:
        verbose_name = 'Discord Auth Settings'
        verbose_name_plural = 'Discord Auth Settings'
        db_table = 'discord_auth_settings'

    def __str__(self):
        return f"Discord Auth Settings (Enabled: {self.enabled})"
