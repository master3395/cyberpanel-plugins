import json
import subprocess
import os
from datetime import datetime, timedelta
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from functools import wraps
from plogical.mailUtilities import mailUtilities
from plogical.httpProc import httpProc
from plogical.acl import ACLManager
from plogical.CyberCPLogFileWriter import CyberCPLogFileWriter as logging
from .models import Fail2banSettings, SecurityEvent, BannedIP, WhitelistIP, BlacklistIP
from .utils import Fail2banManager


def cyberpanel_login_required(view_func):
    """Decorator to check CyberPanel session"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        try:
            userID = request.session['userID']
            return view_func(request, *args, **kwargs)
        except KeyError:
            from loginSystem.views import loadLoginPage
            return redirect(loadLoginPage)
    return _wrapped_view


@cyberpanel_login_required
def fail2ban_plugin(request):
    """Main plugin page (required by CyberPanel)"""
    mailUtilities.checkHome()
    return unified_settings(request)


@cyberpanel_login_required
def plugin_card(request):
    """Plugin card for CyberPanel dashboard"""
    try:
        manager = Fail2banManager()
        status = manager.get_status()
        
        context = {
            'title': 'Fail2ban Security Manager',
            'status': status,
            'plugin_name': 'Fail2ban',
            'version': '1.0.3',
        }
        proc = httpProc(request, 'fail2ban/plugin_card.html', context, 'admin')
        return proc.render()
    except Exception as e:
        return HttpResponse(f"<div>Plugin Card Error: {str(e)}</div>")


@cyberpanel_login_required
def unified_settings(request):
    """Unified settings view with tabs"""
    try:
        mailUtilities.checkHome()
        
        # Get the active tab from URL parameter or hash
        active_tab = request.GET.get('tab', 'overview')
        
        # Detect tab from URL path
        path = request.path_info
        if 'jails' in path:
            active_tab = 'jails'
        elif 'banned-ips' in path or 'banned_ips' in path:
            active_tab = 'banned-ips'
        elif 'whitelist' in path:
            active_tab = 'whitelist'
        elif 'blacklist' in path:
            active_tab = 'blacklist'
        elif 'logs' in path:
            active_tab = 'logs'
        elif 'statistics' in path:
            active_tab = 'statistics'
        elif 'settings' in path:
            active_tab = 'settings'
        
        # Get basic status information
        manager = Fail2banManager()
        status = manager.get_status()
        
        # Get more detailed data for direct template rendering
        jails_list = status.get('jails', [])
        total_jails = status.get('total_jails', len(jails_list))
        is_running = status.get('running', False)
        
        # Get banned IPs count from all jails
        banned_ips_total = 0
        jails_detail = manager.get_jails()
        for jail in jails_detail:
            banned_ips_total += jail.get('banned_ips', 0)
        
        # Get uptime
        uptime_str = 'N/A'
        if is_running:
            try:
                import subprocess
                result = subprocess.run(
                    ['/usr/bin/systemctl', 'show', 'fail2ban', '--property=ActiveEnterTimestamp', '--value'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0 and result.stdout.strip():
                    from datetime import datetime
                    timestamp_str = result.stdout.strip()
                    # Parse timestamp like "Wed 2026-02-01 22:17:36 CET"
                    try:
                        # Try parsing with timezone
                        timestamp_str_clean = ' '.join(timestamp_str.split()[:4])  # Remove timezone
                        start_time = datetime.strptime(timestamp_str_clean, '%a %Y-%m-%d %H:%M:%S')
                        uptime_delta = datetime.now() - start_time
                        days = uptime_delta.days
                        hours, remainder = divmod(uptime_delta.seconds, 3600)
                        minutes, _ = divmod(remainder, 60)
                        if days > 0:
                            uptime_str = f'{days}D, {hours}H, {minutes}M'
                        else:
                            uptime_str = f'{hours}H, {minutes}M'
                    except:
                        uptime_str = 'Running'
            except:
                uptime_str = 'Running'
        
        # Get settings
        settings = Fail2banSettings.get_settings()
        
        context = {
            'title': 'Fail2ban Security Manager',
            'active_tab': active_tab,
            'status': status,
            'settings': settings,
            'plugin_name': 'Fail2ban',
            'version': '1.0.3',
            # Direct values for template rendering (no JavaScript needed)
            'is_running': is_running,
            'jails_count': len(jails_list),
            'total_jails': total_jails,
            'banned_ips_total': banned_ips_total,
            'uptime_str': uptime_str,
            'jails_detail': jails_detail,
            'tabs': [
                {'id': 'overview', 'name': 'Overview', 'icon': '📊'},
                {'id': 'jails', 'name': 'Manage Jails', 'icon': '🔒'},
                {'id': 'banned-ips', 'name': 'Banned IPs', 'icon': '🚫'},
                {'id': 'whitelist', 'name': 'Whitelist', 'icon': '✅'},
                {'id': 'blacklist', 'name': 'Blacklist', 'icon': '⚫'},
                {'id': 'logs', 'name': 'Security Logs', 'icon': '📋'},
                {'id': 'statistics', 'name': 'Statistics', 'icon': '📈'},
                {'id': 'settings', 'name': 'Settings', 'icon': '⚙️'},
            ]
        }
        
        proc = httpProc(request, 'fail2ban/unified_settings.html', context, 'admin')
        return proc.render()
    except Exception as e:
        logging.writeToFile(f"Error in unified_settings: {str(e)}")
        import traceback
        logging.writeToFile(f"Traceback: {traceback.format_exc()}")
        return HttpResponse(f"""
        <div style="padding: 20px; font-family: Arial, sans-serif;">
            <h1 style="color: #f56565;">Plugin Error</h1>
            <p>There was an error loading the Fail2ban plugin settings.</p>
            <p><strong>Error:</strong> {str(e)}</p>
            <p>Please try refreshing the page or contact support if the issue persists.</p>
        </div>
        """, status=500)


@cyberpanel_login_required
def settings_simple(request):
    """Simple settings page (PM2 Manager style) with plugin info and Go To dashboard link"""
    try:
        mailUtilities.checkHome()
        manager = Fail2banManager()
        status = manager.get_status()
        status_label = 'Active' if status.get('running', False) else 'Inactive'
        context = {
            'plugin_name': 'Fail2ban Security Manager',
            'version': '1.0.3',
            'status': status_label,
        }
        proc = httpProc(request, 'fail2ban/settings_simple.html', context, 'admin')
        return proc.render()
    except Exception as e:
        logging.writeToFile(f"Error in settings_simple: {str(e)}")
        context = {
            'plugin_name': 'Fail2ban Security Manager',
            'version': '1.0.3',
            'status': 'Unknown',
        }
        proc = httpProc(request, 'fail2ban/settings_simple.html', context, 'admin')
        return proc.render()


# Legacy views for backward compatibility
@cyberpanel_login_required
def dashboard(request):
    return unified_settings(request)

@cyberpanel_login_required
def settings_standalone(request):
    """Full unified settings with settings tab (use ?tab=settings for direct tab)"""
    return unified_settings(request)

@cyberpanel_login_required
def jails_standalone(request):
    return unified_settings(request)

@cyberpanel_login_required
def banned_ips_standalone(request):
    return unified_settings(request)

@cyberpanel_login_required
def whitelist_standalone(request):
    return unified_settings(request)

@cyberpanel_login_required
def blacklist_standalone(request):
    return unified_settings(request)

@cyberpanel_login_required
def logs_standalone(request):
    return unified_settings(request)

@cyberpanel_login_required
def statistics_standalone(request):
    return unified_settings(request)


# API Endpoints
@cyberpanel_login_required
@require_http_methods(["GET"])
def api_status(request):
    """Get fail2ban service status"""
    try:
        manager = Fail2banManager()
        status = manager.get_status()
        
        # Get banned IPs count
        banned_ips = manager.get_banned_ips()
        
        # Calculate uptime
        uptime = 'N/A'
        try:
            result = subprocess.run(
                ['/usr/bin/systemctl', 'show', 'fail2ban', '--property=ActiveEnterTimestamp', '--value'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                start_time = datetime.fromisoformat(result.stdout.strip().replace(' ', 'T'))
                uptime_delta = datetime.now() - start_time
                days = uptime_delta.days
                hours, remainder = divmod(uptime_delta.seconds, 3600)
                minutes, _ = divmod(remainder, 60)
                uptime = f"{days}D, {hours}H, {minutes}M"
        except:
            pass
        
        running = status.get('running', False)
        jails_list = status.get('jails', [])
        data = {
            'running': running,
            'jails': jails_list,
            'total_jails': status.get('total_jails', len(jails_list)),
            'active_jails': len(jails_list),
            'banned_ips': len(banned_ips),
            'uptime': uptime,
            'status': 'Active' if running else 'Inactive'
        }
        if not running and status.get('error'):
            data['error'] = status.get('error')
        return JsonResponse({'success': True, 'data': data})
    except Exception as e:
        logging.writeToFile(f"api_status error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@cyberpanel_login_required
@require_http_methods(["GET"])
def api_jails(request):
    """Get all jails information"""
    try:
        manager = Fail2banManager()
        jails = manager.get_jails()
        return JsonResponse({
            'success': True,
            'data': jails
        })
    except Exception as e:
        logging.writeToFile(f"api_jails error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@cyberpanel_login_required
@require_http_methods(["GET"])
def api_banned_ips(request):
    """Get all banned IPs"""
    try:
        manager = Fail2banManager()
        banned_ips = manager.get_banned_ips()
        return JsonResponse({
            'success': True,
            'data': banned_ips
        })
    except Exception as e:
        logging.writeToFile(f"api_banned_ips error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@cyberpanel_login_required
@require_http_methods(["GET", "POST", "DELETE"])
def api_whitelist(request):
    """Manage whitelist IPs"""
    try:
        manager = Fail2banManager()
        
        if request.method == 'GET':
            whitelist = manager.get_whitelist()
            # Also get from database
            db_whitelist = WhitelistIP.objects.filter(is_active=True).values('ip_address', 'description', 'added_at')
            return JsonResponse({
                'success': True,
                'data': {
                    'config_ips': whitelist,
                    'db_ips': list(db_whitelist)
                }
            })
        
        elif request.method == 'POST':
            data = json.loads(request.body)
            ip = data.get('ip')
            description = data.get('description', '')
            
            if not ip:
                return JsonResponse({
                    'success': False,
                    'error': 'IP address is required'
                }, status=400)
            
            # Add to database
            whitelist_ip, created = WhitelistIP.objects.get_or_create(
                ip_address=ip,
                defaults={'description': description, 'is_active': True}
            )
            if not created:
                whitelist_ip.is_active = True
                whitelist_ip.description = description
                whitelist_ip.save()
            
            # Add to fail2ban config
            result = manager.add_to_whitelist(ip)
            
            if result.get('success'):
                SecurityEvent.objects.create(
                    event_type='whitelist',
                    ip_address=ip,
                    description=f'IP {ip} added to whitelist',
                    severity='low'
                )
            
            return JsonResponse(result)
        
        elif request.method == 'DELETE':
            data = json.loads(request.body)
            ip = data.get('ip')
            
            if not ip:
                return JsonResponse({
                    'success': False,
                    'error': 'IP address is required'
                }, status=400)
            
            # Remove from database
            WhitelistIP.objects.filter(ip_address=ip).update(is_active=False)
            
            # Remove from fail2ban config
            result = manager.remove_from_whitelist(ip)
            return JsonResponse(result)
    
    except Exception as e:
        logging.writeToFile(f"api_whitelist error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@cyberpanel_login_required
@require_http_methods(["GET", "POST", "DELETE"])
def api_blacklist(request):
    """Manage blacklist IPs"""
    try:
        manager = Fail2banManager()
        
        if request.method == 'GET':
            blacklist = manager.get_blacklist()
            # Also get from database
            db_blacklist = BlacklistIP.objects.filter(is_active=True).values('ip_address', 'description', 'added_at')
            return JsonResponse({
                'success': True,
                'data': {
                    'config_ips': blacklist,
                    'db_ips': list(db_blacklist)
                }
            })
        
        elif request.method == 'POST':
            data = json.loads(request.body)
            ip = data.get('ip')
            description = data.get('description', '')
            
            if not ip:
                return JsonResponse({
                    'success': False,
                    'error': 'IP address is required'
                }, status=400)
            
            # Add to database
            blacklist_ip, created = BlacklistIP.objects.get_or_create(
                ip_address=ip,
                defaults={'description': description, 'is_active': True}
            )
            if not created:
                blacklist_ip.is_active = True
                blacklist_ip.description = description
                blacklist_ip.save()
            
            # Add to firewall
            result = manager.add_to_blacklist(ip)
            
            if result.get('success'):
                SecurityEvent.objects.create(
                    event_type='blacklist',
                    ip_address=ip,
                    description=f'IP {ip} added to blacklist',
                    severity='high'
                )
            
            return JsonResponse(result)
        
        elif request.method == 'DELETE':
            data = json.loads(request.body)
            ip = data.get('ip')
            
            if not ip:
                return JsonResponse({
                    'success': False,
                    'error': 'IP address is required'
                }, status=400)
            
            # Remove from database
            BlacklistIP.objects.filter(ip_address=ip).update(is_active=False)
            
            # Remove from firewall
            result = manager.remove_from_blacklist(ip)
            return JsonResponse(result)
    
    except Exception as e:
        logging.writeToFile(f"api_blacklist error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@cyberpanel_login_required
@require_http_methods(["POST"])
def api_ban_ip(request):
    """Ban an IP address"""
    try:
        data = json.loads(request.body)
        ip = data.get('ip')
        jail = data.get('jail', 'sshd')
        
        if not ip:
            return JsonResponse({
                'success': False,
                'error': 'IP address is required'
            }, status=400)
        
        manager = Fail2banManager()
        result = manager.ban_ip(ip, jail)
        
        if result.get('success'):
            SecurityEvent.objects.create(
                event_type='ban',
                ip_address=ip,
                jail_name=jail,
                description=f'IP {ip} banned from {jail}',
                severity='medium'
            )
        
        return JsonResponse(result)
    except Exception as e:
        logging.writeToFile(f"api_ban_ip error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@cyberpanel_login_required
@require_http_methods(["POST"])
def api_unban_ip(request):
    """Unban an IP address"""
    try:
        data = json.loads(request.body)
        ip = data.get('ip')
        jail = data.get('jail', 'sshd')
        
        if not ip:
            return JsonResponse({
                'success': False,
                'error': 'IP address is required'
            }, status=400)
        
        manager = Fail2banManager()
        result = manager.unban_ip(ip, jail)
        
        if result.get('success'):
            SecurityEvent.objects.create(
                event_type='unban',
                ip_address=ip,
                jail_name=jail,
                description=f'IP {ip} unbanned from {jail}',
                severity='low'
            )
        
        return JsonResponse(result)
    except Exception as e:
        logging.writeToFile(f"api_unban_ip error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@cyberpanel_login_required
@require_http_methods(["POST"])
def api_restart(request):
    """Restart fail2ban service"""
    try:
        manager = Fail2banManager()
        result = manager.restart_service()
        
        if result.get('success'):
            SecurityEvent.objects.create(
                event_type='plugin_toggle',
                description='Fail2ban service restarted',
                severity='low'
            )
        
        return JsonResponse(result)
    except Exception as e:
        logging.writeToFile(f"api_restart error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@cyberpanel_login_required
@require_http_methods(["POST"])
def api_restart_litespeed(request):
    """Restart LiteSpeed service"""
    try:
        result = subprocess.run(
            ['/usr/bin/systemctl', 'restart', 'lscpd'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            return JsonResponse({
                'success': True,
                'message': 'LiteSpeed service restarted successfully'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result.stderr or 'Failed to restart LiteSpeed'
            }, status=500)
    except Exception as e:
        logging.writeToFile(f"api_restart_litespeed error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def _parse_journal_log_line(line):
    """Parse a journalctl line into timestamp and message. Returns dict with message, timestamp, event_type if parseable."""
    import re
    out = {'message': line, 'timestamp': None, 'event_type': 'log', 'ip_address': None, 'jail_name': None}
    # journalctl format: "Feb 02 21:00:00 hostname unit[pid]: message" or ISO
    if not line or len(line) < 20:
        return out
    # Try to extract timestamp at start (e.g. "Feb 02 21:00:00 " or "2025-02-02T21:00:00")
    ts_match = re.match(r'^(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})', line)
    if ts_match:
        try:
            tstr = ts_match.group(1)
            parsed = datetime.strptime(tstr, '%b %d %H:%M:%S')
            parsed = parsed.replace(year=datetime.now().year)
            out['timestamp'] = parsed.isoformat()
        except ValueError:
            pass
    # Infer event type from message
    line_lower = line.lower()
    if 'ban' in line_lower and 'unban' not in line_lower:
        out['event_type'] = 'ban'
    elif 'unban' in line_lower:
        out['event_type'] = 'unban'
    elif 'restart' in line_lower or 'start' in line_lower:
        out['event_type'] = 'plugin_toggle'
    return out


@cyberpanel_login_required
@require_http_methods(["GET"])
def api_logs(request):
    """Get fail2ban logs (journalctl -u fail2ban), formatted for dashboard."""
    try:
        limit = int(request.GET.get('limit', 100))
        limit = min(limit, 500)
        manager = Fail2banManager()
        raw_logs = manager.get_logs(limit)
        formatted_logs = [_parse_journal_log_line(log) for log in raw_logs]
        return JsonResponse({
            'success': True,
            'data': formatted_logs
        })
    except Exception as e:
        logging.writeToFile(f"api_logs error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@cyberpanel_login_required
@require_http_methods(["GET", "POST"])
def api_settings(request):
    """Get or update fail2ban settings"""
    try:
        if request.method == 'GET':
            settings = Fail2banSettings.get_settings()
            return JsonResponse({
                'success': True,
                'data': {
                    'email_notifications': settings.email_notifications,
                    'auto_ban_threshold': settings.auto_ban_threshold,
                    'ban_duration': settings.ban_duration,
                    'enabled_jails': settings.enabled_jails or 'sshd,openlitespeed,cyberpanel'
                }
            })
        
        elif request.method == 'POST':
            data = json.loads(request.body)
            settings = Fail2banSettings.get_settings()
            
            settings.email_notifications = data.get('email_notifications', settings.email_notifications)
            settings.auto_ban_threshold = data.get('auto_ban_threshold', settings.auto_ban_threshold)
            settings.ban_duration = data.get('ban_duration', settings.ban_duration)
            settings.enabled_jails = data.get('enabled_jails', settings.enabled_jails)
            settings.save()
            
            SecurityEvent.objects.create(
                event_type='plugin_toggle',
                description='Fail2ban settings updated',
                severity='low'
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Settings updated successfully'
            })
    
    except Exception as e:
        logging.writeToFile(f"api_settings error: {str(e)}")
        import traceback
        logging.writeToFile(f"Traceback: {traceback.format_exc()}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@cyberpanel_login_required
@require_http_methods(["GET"])
def api_statistics(request):
    """Get security statistics"""
    try:
        # Get statistics from the last 30 days
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        stats = {
            'total_events': SecurityEvent.objects.filter(created_at__gte=thirty_days_ago).count(),
            'total_bans': SecurityEvent.objects.filter(event_type='ban', created_at__gte=thirty_days_ago).count(),
            'total_unbans': SecurityEvent.objects.filter(event_type='unban', created_at__gte=thirty_days_ago).count(),
            'total_attacks': SecurityEvent.objects.filter(event_type='attack', created_at__gte=thirty_days_ago).count(),
            'currently_banned': BannedIP.objects.filter(is_active=True).count(),
            'whitelisted_ips': WhitelistIP.objects.filter(is_active=True).count(),
            'blacklisted_ips': BlacklistIP.objects.filter(is_active=True).count(),
        }
        
        # Get events by day for chart
        events_by_day = []
        for i in range(30):
            day = timezone.now() - timedelta(days=i)
            day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            count = SecurityEvent.objects.filter(created_at__gte=day_start, created_at__lt=day_end).count()
            events_by_day.append({
                'date': day_start.date().isoformat(),
                'count': count
            })
        
        stats['events_by_day'] = list(reversed(events_by_day))
        
        return JsonResponse({
            'success': True,
            'data': stats
        })
    except Exception as e:
        logging.writeToFile(f"api_statistics error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@cyberpanel_login_required
@require_http_methods(["POST"])
def api_toggle_plugin(request):
    """Toggle plugin on/off"""
    try:
        data = json.loads(request.body)
        enabled = data.get('enabled', True)
        
        manager = Fail2banManager()
        
        if enabled:
            result = manager.start_service()
            action = 'enabled'
        else:
            result = manager.stop_service()
            action = 'disabled'
        
        if result.get('success', False):
            SecurityEvent.objects.create(
                event_type='plugin_toggle',
                description=f'Plugin {action}',
                severity='medium'
            )
            
            return JsonResponse({
                'success': True,
                'data': {
                    'enabled': enabled,
                    'message': f'Plugin {action} successfully'
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result.get('error', f'Failed to {action} plugin')
            }, status=500)
    
    except Exception as e:
        logging.writeToFile(f"api_toggle_plugin error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
