# -*- coding: utf-8 -*-
"""Statistics API for Fail2ban plugin."""
from datetime import timedelta

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone

from .models import SecurityEvent, BannedIP
from .panel_auth import cyberpanel_login_and_admin, json_server_error


@cyberpanel_login_and_admin
@require_http_methods(["GET"])
def api_statistics(request):
    """Get security statistics"""
    try:
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
        for event_type, _ in SecurityEvent.EVENT_TYPES:
            stats['events_by_type'][event_type] = SecurityEvent.objects.filter(
                event_type=event_type,
                created_at__gte=thirty_days_ago
            ).count()
        for i in range(7):
            date = timezone.now() - timedelta(days=i)
            stats['events_by_day'][date.strftime('%Y-%m-%d')] = SecurityEvent.objects.filter(
                created_at__date=date.date()
            ).count()
        return JsonResponse({'success': True, 'data': stats})
    except Exception as e:
        return json_server_error(request, e)
