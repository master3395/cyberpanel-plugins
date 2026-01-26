from django.contrib import admin
from .models import Fail2banSettings, SecurityEvent, BannedIP, WhitelistIP, BlacklistIP

@admin.register(Fail2banSettings)
class Fail2banSettingsAdmin(admin.ModelAdmin):
    list_display = ['id', 'email_notifications', 'auto_ban_threshold', 'ban_duration', 'enabled_jails', 'updated_at']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    def has_add_permission(self, request):
        # Only allow one settings instance
        return not Fail2banSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion of the singleton
        return False

@admin.register(SecurityEvent)
class SecurityEventAdmin(admin.ModelAdmin):
    list_display = ['event_type', 'ip_address', 'jail_name', 'severity', 'created_at']
    list_filter = ['event_type', 'severity', 'created_at']
    search_fields = ['ip_address', 'jail_name', 'description']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'

@admin.register(BannedIP)
class BannedIPAdmin(admin.ModelAdmin):
    list_display = ['ip_address', 'jail_name', 'is_active', 'banned_at', 'expires_at']
    list_filter = ['is_active', 'jail_name', 'banned_at']
    search_fields = ['ip_address', 'jail_name']
    readonly_fields = ['banned_at']

@admin.register(WhitelistIP)
class WhitelistIPAdmin(admin.ModelAdmin):
    list_display = ['ip_address', 'is_active', 'added_at', 'description']
    list_filter = ['is_active', 'added_at']
    search_fields = ['ip_address', 'description']
    readonly_fields = ['added_at']

@admin.register(BlacklistIP)
class BlacklistIPAdmin(admin.ModelAdmin):
    list_display = ['ip_address', 'is_active', 'added_at', 'description']
    list_filter = ['is_active', 'added_at']
    search_fields = ['ip_address', 'description']
    readonly_fields = ['added_at']
