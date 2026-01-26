# -*- coding: utf-8 -*-
"""
Discord Authentication Admin Interface
"""

from django.contrib import admin
from .models import DiscordAccount, DiscordAuthSettings


@admin.register(DiscordAccount)
class DiscordAccountAdmin(admin.ModelAdmin):
    list_display = ('discord_username', 'discord_id', 'admin', 'linked_at', 'last_used', 'is_active')
    list_filter = ('is_active', 'linked_at')
    search_fields = ('discord_username', 'discord_id', 'admin__userName', 'discord_email')
    readonly_fields = ('linked_at', 'last_used')


@admin.register(DiscordAuthSettings)
class DiscordAuthSettingsAdmin(admin.ModelAdmin):
    list_display = ('enabled', 'auto_create_users', 'default_acl', 'updated_at')
    readonly_fields = ('updated_at',)
