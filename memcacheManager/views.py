# -*- coding: utf-8 -*-
"""
Memcache Manager Views - status, control, stats, flush, config.
Supports both standard Memcached and LiteSpeed LSMCD.
"""
from django.shortcuts import redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from plogical.httpProc import httpProc
from plogical.mailUtilities import mailUtilities
from functools import wraps
import json

from . import utils


def cyberpanel_login_required(view_func):
    """Decorator to ensure user is logged into CyberPanel."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        try:
            request.session['userID']
            return view_func(request, *args, **kwargs)
        except KeyError:
            from loginSystem.views import loadLoginPage
            return redirect(loadLoginPage)
    return _wrapped_view


@cyberpanel_login_required
@require_http_methods(["GET"])
def main_view(request):
    """Main Memcache Manager page: status, controls, stats, config."""
    try:
        mailUtilities.checkHome()
        
        # Get service status
        status_key, status_msg = utils.get_service_status()
        
        # Get service type for display
        service_type = utils.detect_service_type()
        service_display = 'LSMCD' if service_type == 'lsmcd' else 'Memcached'
        
        # Get stats if installed and running
        stats_data = {}
        stats_error = None
        stats_raw = ''
        if status_key == 'running':
            stats_data, stats_error = utils.get_memcache_stats()
            raw_text, _ = utils.get_memcache_stats_raw()
            stats_raw = raw_text or ''
        
        # Get config
        config_data = {}
        config_error = None
        if utils.is_installed():
            config_data, config_error = utils.get_memcache_config()
        
        # Test connection
        connection_ok = False
        connection_msg = ''
        if status_key == 'running':
            connection_ok, connection_msg = utils.test_connection()
        
        context = {
            'title': 'Memcache Manager',
            'plugin_name': 'Memcache Manager',
            'version': '1.1.0',
            'is_paid': False,
            'installed': utils.is_installed(),
            'service_type': service_type,
            'service_display': service_display,
            'status_key': status_key,
            'status_msg': status_msg,
            'stats_data': stats_data or {},
            'stats_error': stats_error or '',
            'stats_raw': stats_raw,
            'config_data': config_data or {},
            'config_error': config_error or '',
            'connection_ok': connection_ok,
            'connection_msg': connection_msg,
        }
        
        proc = httpProc(request, 'memcacheManager/index.html', context, 'admin')
        return proc.render()
    
    except Exception as e:
        from plogical.CyberCPLogFileWriter import CyberCPLogFileWriter as logging
        logging.writeToFile('Memcache Manager main_view error: %s' % str(e))
        return JsonResponse({'error': str(e)}, status=500)


@cyberpanel_login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_control(request):
    """API: start, stop, restart, enable, disable memcache service."""
    try:
        data = json.loads(request.body) if request.body else {}
        action = (data.get('action') or '').strip().lower()
        
        if action not in ('start', 'stop', 'restart', 'enable', 'disable'):
            return JsonResponse({
                'success': False,
                'error': 'Invalid action. Use: start, stop, restart, enable, disable'
            }, status=400)
        
        ok, msg = utils.service_control(action)
        return JsonResponse({'success': ok, 'message': msg})
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        from plogical.CyberCPLogFileWriter import CyberCPLogFileWriter as logging
        logging.writeToFile('Memcache Manager api_control error: %s' % str(e))
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@cyberpanel_login_required
@require_http_methods(["GET"])
def api_stats(request):
    """API: Get memcache statistics as JSON (for real-time updates)."""
    try:
        if not utils.is_installed():
            return JsonResponse({
                'success': False,
                'error': 'Memcache is not installed.'
            })
        
        status_key, status_msg = utils.get_service_status()
        if status_key != 'running':
            return JsonResponse({
                'success': False,
                'error': 'Memcache service is not running.',
                'status': status_key
            })
        
        stats, error = utils.get_memcache_stats()
        if error:
            return JsonResponse({
                'success': False,
                'error': error
            })
        
        # Format some values for display
        formatted_stats = dict(stats)
        if 'bytes' in formatted_stats:
            formatted_stats['bytes_formatted'] = utils.format_bytes(formatted_stats['bytes'])
        if 'limit_maxbytes' in formatted_stats:
            formatted_stats['limit_maxbytes_formatted'] = utils.format_bytes(
                formatted_stats['limit_maxbytes']
            )
        
        return JsonResponse({
            'success': True,
            'stats': formatted_stats
        })
    
    except Exception as e:
        from plogical.CyberCPLogFileWriter import CyberCPLogFileWriter as logging
        logging.writeToFile('Memcache Manager api_stats error: %s' % str(e))
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@cyberpanel_login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_flush(request):
    """API: Flush all memcache data."""
    try:
        ok, msg = utils.memcache_flush_all()
        return JsonResponse({'success': ok, 'message': msg})
    
    except Exception as e:
        from plogical.CyberCPLogFileWriter import CyberCPLogFileWriter as logging
        logging.writeToFile('Memcache Manager api_flush error: %s' % str(e))
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@cyberpanel_login_required
@require_http_methods(["GET"])
def api_config(request):
    """API: Get memcache configuration as JSON."""
    try:
        if not utils.is_installed():
            return JsonResponse({
                'success': False,
                'error': 'Memcache is not installed.'
            })
        
        config, error = utils.get_memcache_config()
        if error:
            return JsonResponse({
                'success': False,
                'error': error
            })
        
        return JsonResponse({
            'success': True,
            'config': config
        })
    
    except Exception as e:
        from plogical.CyberCPLogFileWriter import CyberCPLogFileWriter as logging
        logging.writeToFile('Memcache Manager api_config error: %s' % str(e))
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
