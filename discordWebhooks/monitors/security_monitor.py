# -*- coding: utf-8 -*-
"""
Security Warning Monitor for Discord Webhooks Plugin
Monitors security-related logs (fail2ban, firewall, etc.) and sends notifications
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
from discordWebhooks.utils import send_to_all_webhooks, format_security_warning_embed

# Security log file paths
FAIL2BAN_LOG = '/var/log/fail2ban.log'
FIREWALL_LOG = '/var/log/messages'  # On RHEL/AlmaLinux, firewall logs may be in messages

# State file to track last read position
STATE_FILE = '/tmp/discord_webhooks_security_monitor.state'

# Security event patterns
FAIL2BAN_BAN_PATTERN = r'\[(?P<jail>\S+)\].*Ban (?P<ip>\S+)'
FAIL2BAN_UNBAN_PATTERN = r'\[(?P<jail>\S+)\].*Unban (?P<ip>\S+)'

def get_last_position(log_path):
    """Get the last read position from state file"""
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, 'r') as f:
                lines = f.readlines()
                for line in lines:
                    data = line.strip().split(':')
                    if len(data) == 2 and data[0] == log_path:
                        return int(data[1])
    except Exception as e:
        logging.writeToFile(f"Error reading state file: {str(e)}")
    return 0

def save_last_position(log_path, position):
    """Save the last read position to state file"""
    try:
        # Read existing positions
        positions = {}
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, 'r') as f:
                for line in f:
                    data = line.strip().split(':')
                    if len(data) == 2:
                        positions[data[0]] = data[1]
        
        # Update position for this log
        positions[log_path] = str(position)
        
        # Write all positions
        with open(STATE_FILE, 'w') as f:
            for path, pos in positions.items():
                f.write(f"{path}:{pos}\n")
    except Exception as e:
        logging.writeToFile(f"Error saving state file: {str(e)}")

def parse_fail2ban_line(line):
    """Parse a fail2ban log line"""
    # Check for ban
    ban_match = re.search(FAIL2BAN_BAN_PATTERN, line)
    if ban_match:
        return {
            'type': 'fail2ban_ban',
            'jail': ban_match.group('jail'),
            'ip': ban_match.group('ip'),
            'severity': 'warning',
            'message': f"IP {ban_match.group('ip')} banned by fail2ban jail '{ban_match.group('jail')}'"
        }
    
    # Check for unban
    unban_match = re.search(FAIL2BAN_UNBAN_PATTERN, line)
    if unban_match:
        return {
            'type': 'fail2ban_unban',
            'jail': unban_match.group('jail'),
            'ip': unban_match.group('ip'),
            'severity': 'info',
            'message': f"IP {unban_match.group('ip')} unbanned from fail2ban jail '{unban_match.group('jail')}'"
        }
    
    return None

def monitor_fail2ban():
    """Monitor fail2ban logs"""
    try:
        if not os.path.exists(FAIL2BAN_LOG):
            return
        
        last_position = get_last_position(FAIL2BAN_LOG)
        
        try:
            with open(FAIL2BAN_LOG, 'r') as f:
                f.seek(last_position)
                new_lines = f.readlines()
                current_position = f.tell()
                
                for line in new_lines:
                    event = parse_fail2ban_line(line)
                    if event:
                        embed = format_security_warning_embed(
                            warning_type=event['type'],
                            message=event['message'],
                            severity=event['severity'],
                            source='fail2ban'
                        )
                        send_to_all_webhooks(embed)
                        logging.writeToFile(f"Security notification sent: {event['type']} - {event['message']}")
                
                if current_position > last_position:
                    save_last_position(FAIL2BAN_LOG, current_position)
                    
        except PermissionError:
            logging.writeToFile(f"Permission denied reading {FAIL2BAN_LOG}")
        except Exception as e:
            logging.writeToFile(f"Error reading fail2ban log: {str(e)}")
            
    except Exception as e:
        logging.writeToFile(f"Fail2ban monitor error: {str(e)}")

def monitor_security_warnings():
    """Main monitoring function"""
    try:
        # Check if security warnings are enabled
        settings = WebhookSettings.get_settings()
        if not settings.security_warnings_enabled:
            return
        
        # Check if there are enabled webhooks
        webhook_count = DiscordWebhook.objects.filter(enabled=True).count()
        if webhook_count == 0:
            return
        
        # Monitor fail2ban
        monitor_fail2ban()
        
        # Add more security monitoring sources here as needed
        
    except Exception as e:
        logging.writeToFile(f"Security monitor error: {str(e)}")

if __name__ == '__main__':
    # Run once when executed directly
    monitor_security_warnings()
