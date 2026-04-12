# -*- coding: utf-8 -*-
"""JSON API views for Fail2ban plugin (CyberPanel admin session required)."""
import json
import subprocess
import uuid
import logging as pylogging

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Fail2banSettings, SecurityEvent
from .utils import Fail2banManager
from .panel_auth import (
    cyberpanel_login_and_admin,
    json_server_error,
    _django_user_for_fail2ban_settings,
)

logger = pylogging.getLogger('fail2ban_plugin')


@cyberpanel_login_and_admin
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
        return json_server_error(request, e)


@cyberpanel_login_and_admin
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
        return json_server_error(request, e)


@cyberpanel_login_and_admin
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
        return json_server_error(request, e)


@cyberpanel_login_and_admin
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
        return json_server_error(request, e)


@cyberpanel_login_and_admin
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
        return json_server_error(request, e)


@cyberpanel_login_and_admin
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

        if not result.get('success'):
            error_id = str(uuid.uuid4())[:12]
            logger.error(
                'ban_ip failed error_id=%s ip=%s jail=%s detail=%s',
                error_id,
                ip,
                jail,
                result.get('error', ''),
            )
            return JsonResponse(
                {
                    'success': False,
                    'error': 'Could not ban IP',
                    'error_id': error_id,
                },
                status=400,
            )

        SecurityEvent.objects.create(
            event_type='ban',
            ip_address=ip,
            jail_name=jail,
            description='IP %s manually banned from %s' % (ip, jail),
            severity='high'
        )

        return JsonResponse({
            'success': True,
            'data': result
        })

    except Exception as e:
        return json_server_error(request, e)


@cyberpanel_login_and_admin
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

        if not result.get('success'):
            error_id = str(uuid.uuid4())[:12]
            logger.error(
                'unban_ip failed error_id=%s ip=%s jail=%s detail=%s',
                error_id,
                ip,
                jail,
                result.get('error', ''),
            )
            return JsonResponse(
                {
                    'success': False,
                    'error': 'Could not unban IP',
                    'error_id': error_id,
                },
                status=400,
            )

        SecurityEvent.objects.create(
            event_type='unban',
            ip_address=ip,
            jail_name=jail,
            description='IP %s manually unbanned from %s' % (ip, jail),
            severity='medium'
        )

        return JsonResponse({
            'success': True,
            'data': result
        })

    except Exception as e:
        return json_server_error(request, e)


@cyberpanel_login_and_admin
@require_http_methods(["POST"])
def api_restart(request):
    """Restart fail2ban service"""
    try:
        manager = Fail2banManager()
        result = manager.restart_service()

        if not result.get('success'):
            error_id = str(uuid.uuid4())[:12]
            logger.error(
                'api_restart failed error_id=%s detail=%s',
                error_id,
                result.get('error', ''),
            )
            return JsonResponse(
                {
                    'success': False,
                    'error': 'Internal server error',
                    'error_id': error_id,
                },
                status=500,
            )

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
        return json_server_error(request, e)


@cyberpanel_login_and_admin
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
        return json_server_error(request, e)


@cyberpanel_login_and_admin
@require_http_methods(["GET", "POST"])
def api_settings(request):
    """Get or update fail2ban settings"""
    try:
        panel_user = _django_user_for_fail2ban_settings(request)
        if request.method == 'GET':
            settings, created = Fail2banSettings.objects.get_or_create(user=panel_user)
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
            settings, created = Fail2banSettings.objects.get_or_create(user=panel_user)

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
        return json_server_error(request, e)


@cyberpanel_login_and_admin
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
                ip_address='0.0.0.0',
                jail_name='system',
                description='Plugin %s by user' % action,
                severity='medium'
            )

            return JsonResponse({
                'success': True,
                'data': {
                    'enabled': enabled,
                    'message': 'Plugin %s successfully' % action
                }
            })
        else:
            error_id = str(uuid.uuid4())[:12]
            logger.error(
                'toggle_plugin failed error_id=%s action=%s detail=%s',
                error_id,
                action,
                result.get('error', ''),
            )
            return JsonResponse(
                {
                    'success': False,
                    'error': 'Internal server error',
                    'error_id': error_id,
                },
                status=500,
            )

    except Exception as e:
        return json_server_error(request, e)


@cyberpanel_login_and_admin
@require_http_methods(["POST"])
def api_restart_litespeed(request):
    """Restart LiteSpeed service"""
    try:
        result = subprocess.run(
            ['systemctl', 'restart', 'lshttpd'],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
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
                }
            })
        else:
            error_id = str(uuid.uuid4())[:12]
            logger.error(
                'litespeed restart failed error_id=%s stderr=%s',
                error_id,
                (result.stderr or '')[:2000],
            )
            return JsonResponse(
                {
                    'success': False,
                    'error': 'Could not restart LiteSpeed',
                    'error_id': error_id,
                },
                status=500,
            )

    except subprocess.TimeoutExpired as e:
        return json_server_error(request, e)
    except Exception as e:
        return json_server_error(request, e)
