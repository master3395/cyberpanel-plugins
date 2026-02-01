from django import forms
from .models import ContaboConfig, SnapshotSchedule


class ContaboConfigForm(forms.ModelForm):
    """Form for Contabo API configuration"""
    class Meta:
        model = ContaboConfig
        fields = ['api_client_id', 'api_client_secret', 'api_key', 'api_secret', 'api_base_url', 
                  'auto_backup_enabled', 'max_snapshots_per_vps', 'payment_method']
        widgets = {
            'api_client_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your Contabo API Client ID'
            }),
            'api_client_secret': forms.PasswordInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your Contabo API Client Secret'
            }),
            'api_key': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your Contabo API Key'
            }),
            'api_secret': forms.PasswordInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your Contabo API Secret'
            }),
            'api_base_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://api.contabo.com/v1'
            }),
            'auto_backup_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'max_snapshots_per_vps': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 100,
                'placeholder': '10'
            }),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
        }
        help_texts = {
            'api_client_id': 'Get this from your Contabo API settings',
            'api_client_secret': 'Get this from your Contabo API settings',
            'api_key': 'Get this from your Contabo API settings',
            'api_secret': 'Get this from your Contabo API settings',
            'auto_backup_enabled': 'Enable or disable automatic snapshots globally. When disabled, all schedules are paused.',
            'max_snapshots_per_vps': 'Maximum snapshots per VPS based on your Contabo plan. Check your plan limits at my.contabo.com',
            'payment_method': 'Choose which payment method to use for verification. "Check Both" will grant access if either Patreon or PayPal is valid.',
        }


class SnapshotScheduleForm(forms.ModelForm):
    """Form for creating/editing snapshot schedules"""
    class Meta:
        model = SnapshotSchedule
        fields = [
            'name', 'vps_id', 'schedule_type', 'cron_expression',
            'snapshot_name_prefix', 'include_ram', 'description_template',
            'retention_count', 'auto_delete_old', 'enabled'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Daily Backup for VPS-123'
            }),
            'vps_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your Contabo VPS Instance ID'
            }),
            'schedule_type': forms.Select(attrs={'class': 'form-control'}),
            'cron_expression': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '0 2 * * * (daily at 2 AM)'
            }),
            'snapshot_name_prefix': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'auto-snapshot'
            }),
            'include_ram': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'description_template': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Auto snapshot created on {date}'
            }),
            'retention_count': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 100,
                'placeholder': '5'
            }),
            'auto_delete_old': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {
            'name': 'A descriptive name for this schedule',
            'vps_id': 'The Contabo VPS instance ID to snapshot',
            'schedule_type': 'How often to create snapshots',
            'cron_expression': 'Custom cron expression (only used if schedule type is Custom)',
            'snapshot_name_prefix': 'Prefix for snapshot names',
            'include_ram': 'Include RAM state in snapshot (may take longer)',
            'description_template': 'Use {date} placeholder for automatic date insertion',
            'retention_count': 'Number of snapshots to keep for this schedule. This will be limited by the global max_snapshots_per_vps setting. Set to 0 to keep all (not recommended).',
            'auto_delete_old': 'Automatically delete old snapshots when limit is reached',
        }

    def clean(self):
        cleaned_data = super().clean()
        schedule_type = cleaned_data.get('schedule_type')
        cron_expression = cleaned_data.get('cron_expression')
        retention_count = cleaned_data.get('retention_count', 0)
        
        # Validate cron expression if schedule type is custom
        if schedule_type == 'custom' and not cron_expression:
            raise forms.ValidationError({
                'cron_expression': 'Cron expression is required when schedule type is Custom.'
            })
        
        # Validate retention count against global max
        from .models import ContaboConfig
        config = ContaboConfig.get_config()
        if config.max_snapshots_per_vps > 0 and retention_count > config.max_snapshots_per_vps:
            raise forms.ValidationError({
                'retention_count': f'Retention count ({retention_count}) cannot exceed the global maximum ({config.max_snapshots_per_vps} snapshots per VPS). Please adjust the global limit in Auto Backup Settings first.'
            })
        
        return cleaned_data


class ManualSnapshotForm(forms.Form):
    """Form for manually creating a snapshot"""
    vps_id = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your Contabo VPS Instance ID'
        }),
        help_text='The Contabo VPS instance ID to snapshot'
    )
    snapshot_name = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'my-manual-snapshot-2025-01-15'
        }),
        help_text='Name for the snapshot'
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Optional description for this snapshot'
        }),
        help_text='Optional description'
    )
    include_ram = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text='Include RAM state in snapshot (may take longer)'
    )
