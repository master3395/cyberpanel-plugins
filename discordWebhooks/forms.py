from django import forms
from .models import DiscordWebhook, WebhookSettings


class DiscordWebhookForm(forms.ModelForm):
    """Form for creating/editing Discord webhook URLs"""
    
    class Meta:
        model = DiscordWebhook
        fields = ['name', 'url', 'enabled']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Webhook name (e.g., Main Server Alerts)'}),
            'url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://discord.com/api/webhooks/...'}),
            'enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }
        labels = {
            'name': 'Webhook Name',
            'url': 'Discord Webhook URL',
            'enabled': 'Enabled'
        }
        help_texts = {
            'url': 'The Discord webhook URL. You can get this from Discord Server Settings > Integrations > Webhooks'
        }


class WebhookSettingsForm(forms.ModelForm):
    """Form for configuring webhook settings"""
    
    class Meta:
        model = WebhookSettings
        fields = [
            'ssh_logins_enabled',
            'security_warnings_enabled',
            'server_usage_enabled',
            'server_usage_cpu',
            'server_usage_memory',
            'server_usage_disk',
            'server_usage_network',
            'server_usage_threshold_mode',
            'cpu_threshold',
            'memory_threshold',
            'disk_threshold',
            'check_interval'
        ]
        widgets = {
            'ssh_logins_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'security_warnings_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'server_usage_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'server_usage_cpu': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'server_usage_memory': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'server_usage_disk': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'server_usage_network': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'server_usage_threshold_mode': forms.RadioSelect(choices=[(True, 'Threshold-based (only notify when exceeded)'), (False, 'All metrics (notify every interval)')]),
            'cpu_threshold': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
            'memory_threshold': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
            'disk_threshold': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
            'check_interval': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 60})
        }
