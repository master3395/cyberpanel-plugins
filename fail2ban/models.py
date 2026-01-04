from django.db import models
from django.contrib.auth.models import User

class Fail2banSettings(models.Model):
    """Store fail2ban plugin settings"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    email_notifications = models.BooleanField(default=True)
    auto_ban_threshold = models.IntegerField(default=5)
    ban_duration = models.IntegerField(default=3600)  # seconds
    whitelist_ips = models.TextField(default='', blank=True)
    blacklist_ips = models.TextField(default='', blank=True)
    enabled_jails = models.TextField(default='sshd,openlitespeed,cyberpanel', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'fail2ban_settings'

class SecurityEvent(models.Model):
    """Log security events and attacks"""
    EVENT_TYPES = [
        ('ban', 'IP Banned'),
        ('unban', 'IP Unbanned'),
        ('attack', 'Attack Detected'),
        ('whitelist', 'IP Whitelisted'),
        ('blacklist', 'IP Blacklisted'),
    ]
    
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    ip_address = models.GenericIPAddressField()
    jail_name = models.CharField(max_length=100, blank=True)
    description = models.TextField()
    severity = models.CharField(max_length=20, default='medium')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'fail2ban_security_events'
        ordering = ['-created_at']

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
