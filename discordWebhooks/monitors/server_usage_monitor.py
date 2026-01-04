# -*- coding: utf-8 -*-
"""
Server Usage Monitor for Discord Webhooks Plugin
Monitors server metrics (CPU, memory, disk, network) and sends notifications
"""
import os
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, '/usr/local/CyberCP')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CyberCP.settings')

import django
django.setup()

from plogical.CyberCPLogFileWriter import CyberCPLogFileWriter as logging
from discordWebhooks.models import DiscordWebhook, WebhookSettings
from discordWebhooks.utils import (
    send_to_all_webhooks, 
    format_server_usage_embed, 
    get_server_metrics, 
    check_server_usage_thresholds
)

# State file to track last notification timestamp (to avoid duplicates)
STATE_FILE = '/tmp/discord_webhooks_server_usage_monitor.state'

# Minimum time between notifications (seconds) - prevents spam
MIN_NOTIFICATION_INTERVAL = 60  # 1 minute (can be overridden by user settings)

def get_last_notification_time():
    """Get the last notification timestamp from state file"""
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, 'r') as f:
                timestamp_str = f.read().strip()
                if timestamp_str:
                    return float(timestamp_str)
    except Exception as e:
        logging.writeToFile(f"Error reading state file: {str(e)}")
    return 0

def save_last_notification_time():
    """Save the current timestamp to state file"""
    try:
        with open(STATE_FILE, 'w') as f:
            f.write(str(datetime.now().timestamp()))
    except Exception as e:
        logging.writeToFile(f"Error saving state file: {str(e)}")

def filter_metrics_by_settings(metrics, settings):
    """Filter metrics based on settings (only include enabled metrics)"""
    filtered = {}
    
    if settings.server_usage_cpu and 'cpu_percent' in metrics:
        filtered['cpu_percent'] = metrics['cpu_percent']
    
    if settings.server_usage_memory and 'memory_percent' in metrics:
        filtered['memory_percent'] = metrics['memory_percent']
    
    if settings.server_usage_disk and 'disk_percent' in metrics:
        filtered['disk_percent'] = metrics['disk_percent']
    
    if settings.server_usage_network and 'network' in metrics:
        filtered['network'] = metrics['network']
    
    return filtered

def monitor_server_usage():
    """Main monitoring function"""
    try:
        # Check if server usage monitoring is enabled
        settings = WebhookSettings.get_settings()
        if not settings.server_usage_enabled:
            return
        
        # Check if there are enabled webhooks
        webhook_count = DiscordWebhook.objects.filter(enabled=True).count()
        if webhook_count == 0:
            return
        
        # Get server metrics
        metrics = get_server_metrics()
        
        # Filter metrics based on settings
        filtered_metrics = filter_metrics_by_settings(metrics, settings)
        
        if not filtered_metrics:
            # No metrics selected, nothing to monitor
            return
        
        # Check if we should send notification
        should_notify = False
        
        if settings.server_usage_threshold_mode:
            # Threshold mode: only notify when thresholds are exceeded
            should_notify = check_server_usage_thresholds(settings, filtered_metrics)
        else:
            # All metrics mode: always notify (but respect minimum interval)
            should_notify = True
        
        if not should_notify:
            return
        
        # Check minimum notification interval to prevent spam
        # Use check_interval from settings (minimum 1 minute is enforced by form validation)
        check_interval_seconds = settings.check_interval * 60
        last_notification = get_last_notification_time()
        current_time = datetime.now().timestamp()
        time_since_last = current_time - last_notification
        
        if time_since_last < check_interval_seconds:
            # Too soon since last notification, skip
            return
        
        # Create embed with filtered metrics
        embed = format_server_usage_embed(
            metrics=filtered_metrics,
            threshold_mode=settings.server_usage_threshold_mode
        )
        
        # Send notification
        result = send_to_all_webhooks(embed)
        
        if result['success_count'] > 0:
            save_last_notification_time()
            logging.writeToFile(f"Server usage notification sent ({result['success_count']} webhooks)")
        else:
            logging.writeToFile(f"Server usage notification failed ({result.get('error', 'Unknown error')})")
            
    except Exception as e:
        logging.writeToFile(f"Server usage monitor error: {str(e)}")

if __name__ == '__main__':
    # Run once when executed directly
    monitor_server_usage()
