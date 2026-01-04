# -*- coding: utf-8 -*-
"""
SSH Login Monitor for Discord Webhooks Plugin
Monitors SSH login attempts and sends notifications to Discord
"""
import os
import re
import sys
import time
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, '/usr/local/CyberCP')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CyberCP.settings')

import django
django.setup()

from plogical.CyberCPLogFileWriter import CyberCPLogFileWriter as logging
from discordWebhooks.models import DiscordWebhook, WebhookSettings
from discordWebhooks.utils import send_to_all_webhooks, format_ssh_login_embed

# SSH log file paths (AlmaLinux/RHEL uses /var/log/secure, Debian/Ubuntu uses /var/log/auth.log)
SSH_LOG_PATHS = [
    '/var/log/secure',
    '/var/log/auth.log'
]

# State file to track last read position
STATE_FILE = '/tmp/discord_webhooks_ssh_monitor.state'

# SSH login patterns
SSH_LOGIN_PATTERNS = [
    r'Accepted (?:publickey|password|keyboard-interactive) for (\S+) from (\S+) port \d+',
    r'Failed (?:password|publickey) for (\S+) from (\S+) port \d+',
]

def get_ssh_log_path():
    """Determine which SSH log file to use based on OS"""
    for path in SSH_LOG_PATHS:
        if os.path.exists(path):
            return path
    return None

def get_last_position(log_path):
    """Get the last read position from state file"""
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, 'r') as f:
                data = f.read().strip().split(':')
                if len(data) == 2 and data[0] == log_path:
                    return int(data[1])
    except Exception as e:
        logging.writeToFile(f"Error reading state file: {str(e)}")
    return 0

def save_last_position(log_path, position):
    """Save the last read position to state file"""
    try:
        with open(STATE_FILE, 'w') as f:
            f.write(f"{log_path}:{position}")
    except Exception as e:
        logging.writeToFile(f"Error saving state file: {str(e)}")

def parse_ssh_log_line(line):
    """Parse an SSH log line and extract login information"""
    for pattern in SSH_LOGIN_PATTERNS:
        match = re.search(pattern, line)
        if match:
            username = match.group(1)
            ip = match.group(2)
            success = 'Accepted' in pattern or 'Accepted' in line
            return {
                'username': username,
                'ip': ip,
                'success': success,
                'timestamp': datetime.now()
            }
    return None

def monitor_ssh_logins():
    """Main monitoring function"""
    try:
        # Check if SSH logins are enabled
        settings = WebhookSettings.get_settings()
        if not settings.ssh_logins_enabled:
            return
        
        # Check if there are enabled webhooks
        webhook_count = DiscordWebhook.objects.filter(enabled=True).count()
        if webhook_count == 0:
            return
        
        # Get SSH log path
        log_path = get_ssh_log_path()
        if not log_path:
            logging.writeToFile("SSH log file not found, skipping SSH login monitoring")
            return
        
        # Get last position
        last_position = get_last_position(log_path)
        
        # Read new lines from log file
        try:
            with open(log_path, 'r') as f:
                # Seek to last position
                f.seek(last_position)
                
                # Read new lines
                new_lines = f.readlines()
                current_position = f.tell()
                
                # Process each new line
                for line in new_lines:
                    login_info = parse_ssh_log_line(line)
                    if login_info:
                        # Send notification
                        embed = format_ssh_login_embed(
                            ip=login_info['ip'],
                            username=login_info['username'],
                            timestamp=login_info['timestamp'],
                            success=login_info['success']
                        )
                        send_to_all_webhooks(embed)
                        logging.writeToFile(f"SSH login notification sent: {login_info['username']} from {login_info['ip']} (success: {login_info['success']})")
                
                # Save new position
                if current_position > last_position:
                    save_last_position(log_path, current_position)
                    
        except PermissionError:
            logging.writeToFile(f"Permission denied reading {log_path}, SSH monitoring may not work correctly")
        except Exception as e:
            logging.writeToFile(f"Error reading SSH log: {str(e)}")
            
    except Exception as e:
        logging.writeToFile(f"SSH monitor error: {str(e)}")

if __name__ == '__main__':
    # Run once when executed directly
    monitor_ssh_logins()
