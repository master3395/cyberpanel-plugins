from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Fail2banSettings(models.Model):
    """Store fail2ban plugin settings - singleton pattern"""
    # Use singleton pattern - only one settings instance
    id = models.IntegerField(primary_key=True, default=1)
    email_notifications = models.BooleanField(default=True)
    auto_ban_threshold = models.IntegerField(default=5)
    ban_duration = models.IntegerField(default=3600)  # seconds
    enabled_jails = models.TextField(default='sshd,openlitespeed,cyberpanel', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'fail2ban_settings'
        verbose_name = 'Fail2ban Settings'
        verbose_name_plural = 'Fail2ban Settings'

    def __str__(self):
        return 'Fail2ban Settings'

    @classmethod
    def get_settings(cls):
        """Get or create the singleton settings instance"""
        settings, created = cls.objects.get_or_create(
            pk=1,
            defaults={
                'email_notifications': True,
                'auto_ban_threshold': 5,
                'ban_duration': 3600,
                'enabled_jails': 'sshd,openlitespeed,cyberpanel'
            }
        )
        return settings

    def save(self, *args, **kwargs):
        """Ensure only one settings instance exists"""
        self.pk = 1
        super(Fail2banSettings, self).save(*args, **kwargs)

class SecurityEvent(models.Model):
    """Log security events and attacks"""
    EVENT_TYPES = [
        ('ban', 'IP Banned'),
        ('unban', 'IP Unbanned'),
        ('attack', 'Attack Detected'),
        ('whitelist', 'IP Whitelisted'),
        ('blacklist', 'IP Blacklisted'),
        ('plugin_toggle', 'Plugin Toggled'),
    ]
    
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    jail_name = models.CharField(max_length=100, blank=True)
    description = models.TextField()
    severity = models.CharField(max_length=20, default='medium')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'fail2ban_security_events'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['event_type']),
            models.Index(fields=['ip_address']),
        ]

    def __str__(self):
        return f"{self.event_type} - {self.ip_address or 'N/A'} - {self.created_at}"

class BannedIP(models.Model):
    """Track currently banned IPs"""
    ip_address = models.GenericIPAddressField(unique=True)
    jail_name = models.CharField(max_length=100)
    ban_reason = models.TextField(blank=True)
    banned_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'fail2ban_banned_ips'
        ordering = ['-banned_at']
        indexes = [
            models.Index(fields=['-banned_at']),
            models.Index(fields=['is_active']),
            models.Index(fields=['jail_name']),
        ]

    def __str__(self):
        return f"{self.ip_address} - {self.jail_name}"

class WhitelistIP(models.Model):
    """Track whitelisted IPs"""
    ip_address = models.GenericIPAddressField(unique=True)
    description = models.TextField(blank=True)
    added_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'fail2ban_whitelist'
        ordering = ['-added_at']

    def __str__(self):
        return f"{self.ip_address}"

class BlacklistIP(models.Model):
    """Track blacklisted IPs"""
    ip_address = models.GenericIPAddressField(unique=True)
    description = models.TextField(blank=True)
    added_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'fail2ban_blacklist'
        ordering = ['-added_at']

    def __str__(self):
        return f"{self.ip_address}"
