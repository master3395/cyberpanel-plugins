from django.db import models
from django.utils import timezone


class DiscordWebhook(models.Model):
    """Model to store Discord webhook URLs"""
    url = models.URLField(max_length=500, help_text="Discord webhook URL")
    name = models.CharField(max_length=100, help_text="User-friendly name for this webhook")
    enabled = models.BooleanField(default=True, help_text="Enable/disable this webhook")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Discord Webhook"
        verbose_name_plural = "Discord Webhooks"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({'Enabled' if self.enabled else 'Disabled'})"


class WebhookSettings(models.Model):
    """Model to store plugin configuration settings (singleton pattern)"""
    # SSH Login Notifications
    ssh_logins_enabled = models.BooleanField(default=False, help_text="Enable SSH login notifications")
    
    # Security Warning Notifications
    security_warnings_enabled = models.BooleanField(default=False, help_text="Enable security warning notifications")
    
    # Server Usage Notifications
    server_usage_enabled = models.BooleanField(default=False, help_text="Enable server usage notifications")
    server_usage_cpu = models.BooleanField(default=True, help_text="Include CPU metrics in server usage notifications")
    server_usage_memory = models.BooleanField(default=True, help_text="Include memory metrics in server usage notifications")
    server_usage_disk = models.BooleanField(default=True, help_text="Include disk metrics in server usage notifications")
    server_usage_network = models.BooleanField(default=False, help_text="Include network metrics in server usage notifications")
    
    # Server Usage Mode: True = threshold-based, False = all metrics
    server_usage_threshold_mode = models.BooleanField(default=True, help_text="Threshold-based notifications (only notify when thresholds exceeded)")
    
    # Thresholds (percentage)
    cpu_threshold = models.IntegerField(default=80, help_text="CPU threshold percentage (0-100)")
    memory_threshold = models.IntegerField(default=80, help_text="Memory threshold percentage (0-100)")
    disk_threshold = models.IntegerField(default=85, help_text="Disk usage threshold percentage (0-100)")
    
    # Monitoring interval in minutes
    check_interval = models.IntegerField(default=5, help_text="Server usage check interval in minutes (minimum 1)")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Webhook Settings"
        verbose_name_plural = "Webhook Settings"

    def __str__(self):
        return "Discord Webhooks Settings"

    @classmethod
    def get_settings(cls):
        """Get or create the singleton settings instance"""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings

    def save(self, *args, **kwargs):
        """Ensure only one settings instance exists"""
        self.pk = 1
        super(WebhookSettings, self).save(*args, **kwargs)
