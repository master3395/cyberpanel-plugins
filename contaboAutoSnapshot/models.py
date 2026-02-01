from django.db import models
from django.utils import timezone


class ContaboConfig(models.Model):
    """Model to store Contabo API credentials (singleton pattern)"""
    api_client_id = models.CharField(max_length=255, blank=True, help_text="Contabo API Client ID")
    api_client_secret = models.CharField(max_length=255, blank=True, help_text="Contabo API Client Secret")
    api_key = models.CharField(max_length=255, blank=True, help_text="Contabo API Key")
    api_secret = models.CharField(max_length=255, blank=True, help_text="Contabo API Secret")
    
    # API endpoint (default to Contabo API v1)
    api_base_url = models.URLField(
        default='https://api.contabo.com/v1',
        help_text="Contabo API Base URL"
    )
    
    # Global auto-backup settings
    auto_backup_enabled = models.BooleanField(
        default=True,
        help_text="Enable/disable automatic snapshots globally. When disabled, all schedules are paused."
    )
    max_snapshots_per_vps = models.IntegerField(
        default=10,
        help_text="Maximum number of snapshots to keep per VPS (based on your Contabo plan limit). Set to 0 for unlimited (not recommended)."
    )
    
    # Payment method preference
    PAYMENT_METHOD_CHOICES = [
        ('patreon', 'Patreon Subscription'),
        ('paypal', 'PayPal Payment'),
        ('both', 'Check Both (Patreon or PayPal)'),
    ]
    payment_method = models.CharField(
        max_length=10,
        choices=PAYMENT_METHOD_CHOICES,
        default='both',
        help_text="Choose which payment method to use for verification. 'Check Both' will grant access if either method is valid."
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Contabo Configuration"
        verbose_name_plural = "Contabo Configurations"

    def __str__(self):
        return "Contabo API Configuration"

    @classmethod
    def get_config(cls):
        """Get or create the singleton config instance"""
        config, created = cls.objects.get_or_create(pk=1)
        return config

    def save(self, *args, **kwargs):
        """Ensure only one config instance exists"""
        self.pk = 1
        super(ContaboConfig, self).save(*args, **kwargs)


class SnapshotSchedule(models.Model):
    """Model to store snapshot schedules"""
    SCHEDULE_CHOICES = [
        ('hourly', 'Hourly'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('custom', 'Custom Cron'),
    ]
    
    name = models.CharField(max_length=100, help_text="Schedule name")
    vps_id = models.CharField(max_length=50, help_text="Contabo VPS Instance ID")
    schedule_type = models.CharField(max_length=20, choices=SCHEDULE_CHOICES, default='daily')
    cron_expression = models.CharField(
        max_length=100, 
        blank=True, 
        help_text="Custom cron expression (e.g., '0 2 * * *' for daily at 2 AM)"
    )
    
    # Snapshot settings
    snapshot_name_prefix = models.CharField(
        max_length=50, 
        default='auto-snapshot',
        help_text="Prefix for snapshot names (e.g., 'auto-snapshot' will create 'auto-snapshot-2025-01-15-10-30')"
    )
    include_ram = models.BooleanField(default=False, help_text="Include RAM state in snapshot")
    description_template = models.CharField(
        max_length=255,
        default='Auto snapshot created on {date}',
        help_text="Description template (use {date} for date placeholder)"
    )
    
    # Retention policy
    retention_count = models.IntegerField(
        default=5,
        help_text="Number of snapshots to keep for this schedule (0 = keep all, but respect global max_snapshots_per_vps limit)"
    )
    auto_delete_old = models.BooleanField(
        default=True,
        help_text="Automatically delete old snapshots when retention limit is reached"
    )
    
    # Status
    enabled = models.BooleanField(default=True, help_text="Enable/disable this schedule")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_run = models.DateTimeField(null=True, blank=True, help_text="Last time this schedule ran")
    next_run = models.DateTimeField(null=True, blank=True, help_text="Next scheduled run time")

    class Meta:
        verbose_name = "Snapshot Schedule"
        verbose_name_plural = "Snapshot Schedules"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.vps_id}) - {self.schedule_type}"


class SnapshotHistory(models.Model):
    """Model to track snapshot creation history"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('creating', 'Creating'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    schedule = models.ForeignKey(
        SnapshotSchedule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Schedule that created this snapshot (null if manual)"
    )
    vps_id = models.CharField(max_length=50, help_text="Contabo VPS Instance ID")
    snapshot_name = models.CharField(max_length=255, help_text="Snapshot name")
    snapshot_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="Contabo snapshot ID (if available)"
    )
    description = models.TextField(blank=True, help_text="Snapshot description")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True, help_text="Error message if snapshot failed")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Snapshot History"
        verbose_name_plural = "Snapshot History"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.snapshot_name} - {self.status}"
