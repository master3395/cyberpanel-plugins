# -*- coding: utf-8 -*-
import requests
import json
import psutil
import subprocess
from datetime import datetime
from plogical.CyberCPLogFileWriter import CyberCPLogFileWriter as logging
from .models import DiscordWebhook, WebhookSettings


def send_discord_webhook(url, embed_data, timeout=10):
    """
    Send a Discord webhook with error handling
    
    Args:
        url: Discord webhook URL
        embed_data: Dictionary containing embed data or message content
        timeout: Request timeout in seconds
        
    Returns:
        dict: {'success': bool, 'message': str, 'status_code': int}
    """
    try:
        # Validate URL
        if not url or not url.startswith('https://discord.com/api/webhooks/'):
            return {
                'success': False,
                'message': 'Invalid Discord webhook URL',
                'status_code': 0
            }
        
        # Prepare payload
        if isinstance(embed_data, dict) and 'embeds' in embed_data:
            payload = embed_data
        elif isinstance(embed_data, dict):
            # If it's a single embed dict, wrap it
            payload = {'embeds': [embed_data]}
        else:
            # Plain text message
            payload = {'content': str(embed_data)}
        
        # Send request
        response = requests.post(
            url,
            json=payload,
            timeout=timeout,
            headers={'Content-Type': 'application/json'}
        )
        
        # Check response
        if response.status_code in [200, 204]:
            return {
                'success': True,
                'message': 'Webhook sent successfully',
                'status_code': response.status_code
            }
        else:
            return {
                'success': False,
                'message': f'Discord API error: {response.status_code}',
                'status_code': response.status_code,
                'response': response.text[:200]  # First 200 chars of response
            }
            
    except requests.exceptions.Timeout:
        return {
            'success': False,
            'message': 'Request timeout',
            'status_code': 0
        }
    except requests.exceptions.RequestException as e:
        logging.writeToFile(f"Discord webhook error: {str(e)}")
        return {
            'success': False,
            'message': f'Request error: {str(e)}',
            'status_code': 0
        }
    except Exception as e:
        logging.writeToFile(f"Discord webhook unexpected error: {str(e)}")
        return {
            'success': False,
            'message': f'Unexpected error: {str(e)}',
            'status_code': 0
        }


def format_ssh_login_embed(ip, username, timestamp, success=True):
    """
    Format SSH login notification embed
    
    Args:
        ip: IP address of login
        username: Username that logged in
        timestamp: Login timestamp
        success: Whether login was successful
        
    Returns:
        dict: Discord embed dictionary
    """
    color = 3066993 if success else 15158332  # Green for success, red for failure
    title = "SSH Login Successful" if success else "SSH Login Failed"
    
    # Logo URL for newstargeted.com branding
    LOGO_URL = 'https://newstargeted.com/hotlink-ok/logo.png'
    
    embed = {
        'title': title,
        'color': color,
        'fields': [
            {
                'name': 'Username',
                'value': username,
                'inline': True
            },
            {
                'name': 'IP Address',
                'value': ip,
                'inline': True
            },
            {
                'name': 'Timestamp',
                'value': timestamp.strftime('%Y-%m-%d %H:%M:%S UTC') if isinstance(timestamp, datetime) else str(timestamp),
                'inline': False
            }
        ],
        'thumbnail': {
            'url': LOGO_URL
        },
        'footer': {
            'text': 'Powered by newstargeted.com',
            'icon_url': LOGO_URL
        },
        'author': {
            'name': 'CyberPanel Discord Webhooks',
            'icon_url': LOGO_URL
        },
        'timestamp': timestamp.isoformat() if isinstance(timestamp, datetime) else datetime.now().isoformat()
    }
    
    return embed


def format_security_warning_embed(warning_type, message, severity='warning', source='System'):
    """
    Format security warning embed
    
    Args:
        warning_type: Type of warning (e.g., 'fail2ban_ban', 'firewall_block')
        message: Warning message
        severity: Severity level ('info', 'warning', 'error', 'critical')
        source: Source of the warning
        
    Returns:
        dict: Discord embed dictionary
    """
    # Color mapping
    color_map = {
        'info': 3447003,      # Blue
        'warning': 15844367,  # Gold
        'error': 15158332,    # Red
        'critical': 10038562  # Dark red
    }
    color = color_map.get(severity.lower(), 15844367)
    
    # Logo URL for newstargeted.com branding
    LOGO_URL = 'https://newstargeted.com/hotlink-ok/logo.png'
    
    embed = {
        'title': f'Security Warning: {warning_type}',
        'description': message,
        'color': color,
        'fields': [
            {
                'name': 'Severity',
                'value': severity.upper(),
                'inline': True
            },
            {
                'name': 'Source',
                'value': source,
                'inline': True
            }
        ],
        'thumbnail': {
            'url': LOGO_URL
        },
        'footer': {
            'text': 'Powered by newstargeted.com',
            'icon_url': LOGO_URL
        },
        'author': {
            'name': 'CyberPanel Discord Webhooks',
            'icon_url': LOGO_URL
        },
        'timestamp': datetime.now().isoformat()
    }
    
    return embed


def format_server_usage_embed(metrics, threshold_mode=True):
    """
    Format server usage metrics embed
    
    Args:
        metrics: Dictionary with CPU, memory, disk, network metrics
        threshold_mode: Whether thresholds were exceeded (affects color)
        
    Returns:
        dict: Discord embed dictionary
    """
    # Determine color based on threshold mode and values
    max_usage = max([
        metrics.get('cpu_percent', 0),
        metrics.get('memory_percent', 0),
        metrics.get('disk_percent', 0)
    ])
    
    if max_usage >= 90:
        color = 15158332  # Red
    elif max_usage >= 70:
        color = 15844367  # Gold
    else:
        color = 3066993  # Green
    
    fields = []
    
    if metrics.get('cpu_percent') is not None:
        fields.append({
            'name': 'CPU Usage',
            'value': f"{metrics['cpu_percent']:.1f}%",
            'inline': True
        })
    
    if metrics.get('memory_percent') is not None:
        fields.append({
            'name': 'Memory Usage',
            'value': f"{metrics['memory_percent']:.1f}%",
            'inline': True
        })
    
    if metrics.get('disk_percent') is not None:
        fields.append({
            'name': 'Disk Usage',
            'value': f"{metrics['disk_percent']:.1f}%",
            'inline': True
        })
    
    if metrics.get('network') is not None:
        fields.append({
            'name': 'Network',
            'value': metrics['network'],
            'inline': False
        })
    
    # Logo URL for newstargeted.com branding
    LOGO_URL = 'https://newstargeted.com/hotlink-ok/logo.png'
    
    embed = {
        'title': 'Server Usage Metrics',
        'color': color,
        'fields': fields,
        'thumbnail': {
            'url': LOGO_URL
        },
        'footer': {
            'text': 'Powered by newstargeted.com',
            'icon_url': LOGO_URL
        },
        'author': {
            'name': 'CyberPanel Discord Webhooks',
            'icon_url': LOGO_URL,
            'url': 'https://newstargeted.com'
        },
        'timestamp': datetime.now().isoformat()
    }
    
    return embed


def get_server_metrics():
    """
    Get current server metrics (CPU, memory, disk, network)
    
    Returns:
        dict: Dictionary with metrics
    """
    try:
        metrics = {}
        
        # CPU usage
        try:
            metrics['cpu_percent'] = psutil.cpu_percent(interval=1)
        except:
            # Fallback to load average
            try:
                with open('/proc/loadavg', 'r') as f:
                    load_avg = float(f.read().split()[0])
                    metrics['cpu_percent'] = min(load_avg * 100, 100)
            except:
                metrics['cpu_percent'] = 0
        
        # Memory usage
        try:
            mem = psutil.virtual_memory()
            metrics['memory_percent'] = mem.percent
            metrics['memory_total'] = mem.total
            metrics['memory_used'] = mem.used
            metrics['memory_available'] = mem.available
        except:
            metrics['memory_percent'] = 0
        
        # Disk usage (root partition)
        try:
            disk = psutil.disk_usage('/')
            metrics['disk_percent'] = disk.percent
            metrics['disk_total'] = disk.total
            metrics['disk_used'] = disk.used
            metrics['disk_free'] = disk.free
        except:
            metrics['disk_percent'] = 0
        
        # Network usage (simplified)
        try:
            net_io = psutil.net_io_counters()
            metrics['network'] = f"Sent: {net_io.bytes_sent / 1024 / 1024 / 1024:.2f} GB, Recv: {net_io.bytes_recv / 1024 / 1024 / 1024:.2f} GB"
        except:
            metrics['network'] = "N/A"
        
        return metrics
        
    except Exception as e:
        logging.writeToFile(f"Error getting server metrics: {str(e)}")
        return {
            'cpu_percent': 0,
            'memory_percent': 0,
            'disk_percent': 0,
            'network': 'Error'
        }


def check_server_usage_thresholds(settings, metrics):
    """
    Check if server usage thresholds are exceeded
    
    Args:
        settings: WebhookSettings instance
        metrics: Dictionary with metrics from get_server_metrics()
        
    Returns:
        bool: True if any threshold is exceeded
    """
    try:
        # Check CPU
        if settings.server_usage_cpu and metrics.get('cpu_percent', 0) >= settings.cpu_threshold:
            return True
        
        # Check Memory
        if settings.server_usage_memory and metrics.get('memory_percent', 0) >= settings.memory_threshold:
            return True
        
        # Check Disk
        if settings.server_usage_disk and metrics.get('disk_percent', 0) >= settings.disk_threshold:
            return True
        
        return False
        
    except Exception as e:
        logging.writeToFile(f"Error checking thresholds: {str(e)}")
        return False


def send_to_all_webhooks(embed_data):
    """
    Send embed data to all enabled webhooks
    
    Args:
        embed_data: Dictionary containing embed data
        
    Returns:
        dict: Summary of sends {'success_count': int, 'fail_count': int, 'results': list}
    """
    try:
        webhooks = DiscordWebhook.objects.filter(enabled=True)
        results = []
        success_count = 0
        fail_count = 0
        
        for webhook in webhooks:
            result = send_discord_webhook(webhook.url, embed_data)
            results.append({
                'webhook_id': webhook.id,
                'webhook_name': webhook.name,
                'success': result['success'],
                'message': result['message']
            })
            
            if result['success']:
                success_count += 1
            else:
                fail_count += 1
                logging.writeToFile(f"Failed to send webhook to {webhook.name}: {result['message']}")
        
        return {
            'success_count': success_count,
            'fail_count': fail_count,
            'results': results
        }
        
    except Exception as e:
        logging.writeToFile(f"Error sending to all webhooks: {str(e)}")
        return {
            'success_count': 0,
            'fail_count': 0,
            'results': [],
            'error': str(e)
        }
