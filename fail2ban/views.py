import json
import subprocess
import os
import re
from datetime import datetime, timedelta
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.utils import timezone
from functools import wraps
from plogical.mailUtilities import mailUtilities
from plogical.httpProc import httpProc
from .models import Fail2banSettings, SecurityEvent, BannedIP
from .utils import Fail2banManager

def cyberpanel_login_required(view_func):
    """
    Custom decorator that checks for CyberPanel session userID
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        try:
            userID = request.session['userID']
            # User is authenticated via CyberPanel session
            return view_func(request, *args, **kwargs)
        except KeyError:
            # Not logged in, redirect to login
            from loginSystem.views import loadLoginPage
            return redirect(loadLoginPage)
    return _wrapped_view

@cyberpanel_login_required
def fail2ban_plugin(request):
    """Main plugin page (required by CyberPanel)"""
    try:
        mailUtilities.checkHome()
        manager = Fail2banManager()
        status = manager.get_status()
        
        context = {
            'title': 'Fail2ban Security Manager',
            'status': status,
        }
        proc = httpProc(request, 'fail2ban/dashboard.html', context, 'admin')
        return proc.render()
    except Exception as e:
        return HttpResponse(f"<div>Plugin Error: {str(e)}</div>")

@cyberpanel_login_required
def plugin_card(request):
    """Plugin card view with buttons"""
    try:
        mailUtilities.checkHome()
        context = {
            'title': 'Settings Plugin Card'
        }
        proc = httpProc(request, 'fail2ban/plugin_card.html', context, 'admin')
        return proc.render()
    except Exception as e:
        return HttpResponse(f"<div>Plugin Card Error: {str(e)}</div>")

@cyberpanel_login_required
def dashboard(request):
    """Standalone dashboard page"""
    try:
        mailUtilities.checkHome()
        manager = Fail2banManager()
        status = manager.get_status()
        
        context = {
            'title': 'Fail2ban Dashboard',
            'status': status,
        }
        proc = httpProc(request, 'fail2ban/dashboard.html', context, 'admin')
        return proc.render()
    except Exception as e:
        return HttpResponse(f"<div>Dashboard Error: {str(e)}</div>")

@cyberpanel_login_required
def jails_standalone(request):
    """Standalone jails management page"""
    try:
        mailUtilities.checkHome()
        manager = Fail2banManager()
        jails = manager.get_jails()
        
        context = {
            'title': 'Jail Management',
            'jails': jails,
        }
        proc = httpProc(request, 'fail2ban/jails_standalone.html', context, 'admin')
        return proc.render()
    except Exception as e:
        return HttpResponse(f"<div>Jails Error: {str(e)}</div>")

@cyberpanel_login_required
def banned_ips_standalone(request):
    """Standalone banned IPs page"""
    try:
        mailUtilities.checkHome()
        manager = Fail2banManager()
        banned_ips = manager.get_banned_ips()
        
        context = {
            'title': 'Banned IPs',
            'banned_ips': banned_ips,
        }
        proc = httpProc(request, 'fail2ban/banned_ips_standalone.html', context, 'admin')
        return proc.render()
    except Exception as e:
        return HttpResponse(f"<div>Banned IPs Error: {str(e)}</div>")

@cyberpanel_login_required
def whitelist_standalone(request):
    """Standalone whitelist page"""
    try:
        mailUtilities.checkHome()
        manager = Fail2banManager()
        whitelist = manager.get_whitelist()
        
        context = {
            'title': 'IP Whitelist Management',
            'whitelist': whitelist,
        }
        proc = httpProc(request, 'fail2ban/whitelist_standalone.html', context, 'admin')
        return proc.render()
    except Exception as e:
        return HttpResponse(f"<div>Whitelist Error: {str(e)}</div>")

@cyberpanel_login_required
def blacklist_standalone(request):
    """Standalone blacklist page"""
    try:
        mailUtilities.checkHome()
        manager = Fail2banManager()
        blacklist = manager.get_blacklist()
        
        context = {
            'title': 'IP Blacklist Management',
            'blacklist': blacklist,
        }
        proc = httpProc(request, 'fail2ban/blacklist_standalone.html', context, 'admin')
        return proc.render()
    except Exception as e:
        return HttpResponse(f"<div>Blacklist Error: {str(e)}</div>")

@cyberpanel_login_required
def logs_standalone(request):
    """Standalone logs page"""
    try:
        mailUtilities.checkHome()
        context = {
            'title': 'Security Logs',
        }
        proc = httpProc(request, 'fail2ban/logs_standalone.html', context, 'admin')
        return proc.render()
    except Exception as e:
        return HttpResponse(f"<div>Logs Error: {str(e)}</div>")

@cyberpanel_login_required
def statistics_standalone(request):
    """Standalone statistics page"""
    try:
        mailUtilities.checkHome()
        context = {
            'title': 'Security Statistics',
        }
        proc = httpProc(request, 'fail2ban/statistics_standalone.html', context, 'admin')
        return proc.render()
    except Exception as e:
        return HttpResponse(f"<div>Statistics Error: {str(e)}</div>")

@cyberpanel_login_required
def settings_standalone(request):
    """Standalone settings page"""
    try:
        mailUtilities.checkHome()
        # Get basic status information
        manager = Fail2banManager()
        status = manager.get_status()
        
        context = {
            'title': 'Settings',
            'plugin_name': 'Fail2ban Security Manager',
            'version': '1.0.0',
            'status': 'Active',
            'plugin_status': 'Active',
            'description': 'Advanced fail2ban management with real-time monitoring and comprehensive security features',
            'status_info': status,
        }
        proc = httpProc(request, 'fail2ban/settings.html', context, 'admin')
        return proc.render()
    except Exception as e:
        return HttpResponse(f"<div>Settings Error: {str(e)}</div>")

@cyberpanel_login_required
def unified_settings(request):
    """Unified settings view with tabs"""
    try:
        # Get the active tab from URL parameter or detect from URL path
        active_tab = request.GET.get('tab', 'overview')
        
        # Detect tab from URL path if no tab parameter
        if active_tab == 'overview':
            path = request.path_info
            if 'jails' in path:
                active_tab = 'jails'
            elif 'banned-ips' in path:
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
        
        context = {
            'title': 'Settings',
            'plugin_name': 'Fail2ban Security Manager',
            'version': '1.0.0',
            'plugin_status': 'Active',
            'active_tab': active_tab,
            'status': status,
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
        proc = httpProc(request, 'fail2ban/clean_settings.html', context, 'admin')
        return proc.render()
    except Exception as e:
        # Log the error and return a proper error response
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in unified_settings: {str(e)}")
        
        # Return a simple error page if there's an issue
        from django.http import HttpResponse
        return HttpResponse(f"""
        <div style="padding: 20px; font-family: Arial, sans-serif;">
            <h1 style="color: #f56565;">Plugin Error</h1>
            <p>There was an error loading the Fail2ban plugin settings.</p>
            <p><strong>Error:</strong> {str(e)}</p>
            <p>Please try refreshing the page or contact support if the issue persists.</p>
        </div>
        """, status=500)

@cyberpanel_login_required
def dashboard_legacy(request):
    """Legacy dashboard view - redirects to unified settings"""
    return unified_settings(request)

@cyberpanel_login_required
def jails_management(request):
    """Jails management page"""
    mailUtilities.checkHome()
    context = {
        'title': 'Jails Management',
        'active_tab': 'jails'
    }
    proc = httpProc(request, 'fail2ban/jails.html', context, 'admin')
    return proc.render()

@cyberpanel_login_required
def banned_ips_management(request):
    """Banned IPs management page"""
    mailUtilities.checkHome()
    context = {
        'title': 'Banned IPs Management',
        'active_tab': 'banned_ips'
    }
    proc = httpProc(request, 'fail2ban/banned_ips.html', context, 'admin')
    return proc.render()

@cyberpanel_login_required
def whitelist_management(request):
    """Whitelist management page"""
    mailUtilities.checkHome()
    context = {
        'title': 'Whitelist Management',
        'active_tab': 'whitelist'
    }
    proc = httpProc(request, 'fail2ban/whitelist.html', context, 'admin')
    return proc.render()

@cyberpanel_login_required
def blacklist_management(request):
    """Blacklist management page"""
    mailUtilities.checkHome()
    context = {
        'title': 'Blacklist Management',
        'active_tab': 'blacklist'
    }
    proc = httpProc(request, 'fail2ban/blacklist.html', context, 'admin')
    return proc.render()

@cyberpanel_login_required
def settings_management(request):
    """Settings management page"""
    mailUtilities.checkHome()
    context = {
        'title': 'Settings Management',
        'active_tab': 'settings'
    }
    proc = httpProc(request, 'fail2ban/settings.html', context, 'admin')
    return proc.render()

@cyberpanel_login_required
def logs_view(request):
    """Logs view page"""
    mailUtilities.checkHome()
    context = {
        'title': 'Security Logs',
        'active_tab': 'logs'
    }
    proc = httpProc(request, 'fail2ban/logs.html', context, 'admin')
    return proc.render()

@cyberpanel_login_required
def statistics_view(request):
    """Statistics view page"""
    mailUtilities.checkHome()
    context = {
        'title': 'Security Statistics',
        'active_tab': 'statistics'
    }
    proc = httpProc(request, 'fail2ban/statistics.html', context, 'admin')
    return proc.render()

# API Views
@cyberpanel_login_required
@require_http_methods(["GET"])
def api_status(request):
    """Get fail2ban service status"""
    try:
        manager = Fail2banManager()
        status = manager.get_status()
        return JsonResponse({
            'success': True,
            'data': status
        })
    except Exception as e:
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
            return JsonResponse({
                'success': True,
                'data': whitelist
            })
        
        elif request.method == 'POST':
            data = json.loads(request.body)
            ip = data.get('ip')
            if not ip:
                return JsonResponse({
                    'success': False,
                    'error': 'IP address is required'
                }, status=400)
            
            result = manager.add_to_whitelist(ip)
            return JsonResponse({
                'success': True,
                'data': result
            })
        
        elif request.method == 'DELETE':
            data = json.loads(request.body)
            ip = data.get('ip')
            if not ip:
                return JsonResponse({
                    'success': False,
                    'error': 'IP address is required'
                }, status=400)
            
            result = manager.remove_from_whitelist(ip)
            return JsonResponse({
                'success': True,
                'data': result
            })
    
    except Exception as e:
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
            return JsonResponse({
                'success': True,
                'data': blacklist
            })
        
        elif request.method == 'POST':
            data = json.loads(request.body)
            ip = data.get('ip')
            if not ip:
                return JsonResponse({
                    'success': False,
                    'error': 'IP address is required'
                }, status=400)
            
            result = manager.add_to_blacklist(ip)
            return JsonResponse({
                'success': True,
                'data': result
            })
        
        elif request.method == 'DELETE':
            data = json.loads(request.body)
            ip = data.get('ip')
            if not ip:
                return JsonResponse({
                    'success': False,
                    'error': 'IP address is required'
                }, status=400)
            
            result = manager.remove_from_blacklist(ip)
            return JsonResponse({
                'success': True,
                'data': result
            })
    
    except Exception as e:
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
        
        # Log the event
        SecurityEvent.objects.create(
            event_type='ban',
            ip_address=ip,
            jail_name=jail,
            description=f'IP {ip} manually banned from {jail}',
            severity='high'
        )
        
        return JsonResponse({
            'success': True,
            'data': result
        })
    
    except Exception as e:
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
        
        # Log the event
        SecurityEvent.objects.create(
            event_type='unban',
            ip_address=ip,
            jail_name=jail,
            description=f'IP {ip} manually unbanned from {jail}',
            severity='medium'
        )
        
        return JsonResponse({
            'success': True,
            'data': result
        })
    
    except Exception as e:
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
        
        # Log the event
        SecurityEvent.objects.create(
            event_type='restart',
            ip_address='0.0.0.0',
            jail_name='system',
            description='Fail2ban service restarted',
            severity='medium'
        )
        
        return JsonResponse({
            'success': True,
            'data': result
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@cyberpanel_login_required
@require_http_methods(["GET"])
def api_logs(request):
    """Get fail2ban logs"""
    try:
        manager = Fail2banManager()
        logs = manager.get_logs()
        return JsonResponse({
            'success': True,
            'data': logs
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@cyberpanel_login_required
@csrf_exempt
@require_http_methods(["GET", "POST"])
def api_settings(request):
    """Get or update fail2ban settings"""
    try:
        # Get Administrator from CyberPanel session
        from loginSystem.models import Administrator
        from django.contrib.auth.models import User
        userID = request.session['userID']
        admin = Administrator.objects.get(pk=userID)
        
        # Get or create Django User for this Administrator
        # CyberPanel uses Administrator model, but our settings model uses User
        # Create a User if it doesn't exist (one-to-one mapping)
        # Use select_related to avoid triggering reverse relationships that might cause errors
        try:
            user = User.objects.get(username=admin.userName)
        except User.DoesNotExist:
            # Create user without triggering signals that might access other plugin tables
            user = User(
                username=admin.userName,
                email=admin.email if hasattr(admin, 'email') else '',
                first_name=admin.firstName if hasattr(admin, 'firstName') else '',
                last_name=admin.lastName if hasattr(admin, 'lastName') else '',
            )
            user.save()
        
        if request.method == 'GET':
            settings, created = Fail2banSettings.objects.get_or_create(user=user)
            return JsonResponse({
                'success': True,
                'data': {
                    'email_notifications': settings.email_notifications,
                    'auto_ban_threshold': settings.auto_ban_threshold,
                    'ban_duration': settings.ban_duration,
                    'whitelist_ips': settings.whitelist_ips,
                    'blacklist_ips': settings.blacklist_ips,
                    'enabled_jails': settings.enabled_jails
                }
            })
        
        elif request.method == 'POST':
            data = json.loads(request.body)
            try:
                settings = Fail2banSettings.objects.get(user=user)
            except Fail2banSettings.DoesNotExist:
                settings = Fail2banSettings.objects.create(user=user)
            
            settings.email_notifications = data.get('email_notifications', settings.email_notifications)
            settings.auto_ban_threshold = data.get('auto_ban_threshold', settings.auto_ban_threshold)
            settings.ban_duration = data.get('ban_duration', settings.ban_duration)
            settings.whitelist_ips = data.get('whitelist_ips', settings.whitelist_ips)
            settings.blacklist_ips = data.get('blacklist_ips', settings.blacklist_ips)
            settings.enabled_jails = data.get('enabled_jails', settings.enabled_jails)
            settings.save()
            
            return JsonResponse({
                'success': True,
                'data': 'Settings updated successfully'
            })
    
    except Exception as e:
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
            'banned_ips': SecurityEvent.objects.filter(event_type='ban', created_at__gte=thirty_days_ago).count(),
            'unbanned_ips': SecurityEvent.objects.filter(event_type='unban', created_at__gte=thirty_days_ago).count(),
            'attacks_detected': SecurityEvent.objects.filter(event_type='attack', created_at__gte=thirty_days_ago).count(),
            'currently_banned': BannedIP.objects.filter(is_active=True).count(),
            'events_by_type': {},
            'events_by_day': {}
        }
        
        # Events by type
        for event_type, _ in SecurityEvent.EVENT_TYPES:
            count = SecurityEvent.objects.filter(
                event_type=event_type,
                created_at__gte=thirty_days_ago
            ).count()
            stats['events_by_type'][event_type] = count
        
        # Events by day (last 7 days)
        for i in range(7):
            date = timezone.now() - timedelta(days=i)
            count = SecurityEvent.objects.filter(
                created_at__date=date.date()
            ).count()
            stats['events_by_day'][date.strftime('%Y-%m-%d')] = count
        
        return JsonResponse({
            'success': True,
            'data': stats
        })
    
    except Exception as e:
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
            # Log the event
            SecurityEvent.objects.create(
                event_type='plugin_toggle',
                ip_address='0.0.0.0',
                jail_name='system',
                description=f'Plugin {action} by user',
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
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@cyberpanel_login_required
@require_http_methods(["POST"])
def api_restart_litespeed(request):
    """Restart LiteSpeed service"""
    try:
        # Restart LiteSpeed service
        result = subprocess.run(
            ['systemctl', 'restart', 'lshttpd'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            # Log the event
            SecurityEvent.objects.create(
                event_type='service_restart',
                ip_address='0.0.0.0',
                jail_name='system',
                description='LiteSpeed service restarted by user',
                severity='medium'
            )
            
            return JsonResponse({
                'success': True,
                'data': {
                    'message': 'LiteSpeed service restarted successfully',
                    'output': result.stdout
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'error': f'Failed to restart LiteSpeed: {result.stderr}'
            }, status=500)
    
    except subprocess.TimeoutExpired:
        return JsonResponse({
            'success': False,
            'error': 'LiteSpeed restart timed out'
        }, status=500)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
