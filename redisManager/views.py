# -*- coding: utf-8 -*-
"""
Redis Manager Views - status, control, stats, flush.
"""
from django.shortcuts import redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie
from plogical.httpProc import httpProc
from plogical.mailUtilities import mailUtilities
from functools import wraps
import json
import uuid

from . import utils


def _redis_json_server_error(request, log_prefix, exc=None):
    error_id = str(uuid.uuid4())[:12]
    from plogical.CyberCPLogFileWriter import CyberCPLogFileWriter as logging

    if exc is not None:
        logging.writeToFile('%s [error_id=%s] %s' % (log_prefix, error_id, str(exc)))
    else:
        logging.writeToFile('%s [error_id=%s]' % (log_prefix, error_id))
    return JsonResponse(
        {'success': False, 'error': 'Internal server error', 'error_id': error_id},
        status=500,
    )


def cyberpanel_login_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        try:
            request.session['userID']
            return view_func(request, *args, **kwargs)
        except KeyError:
            from loginSystem.views import loadLoginPage
            return redirect(loadLoginPage)
    return _wrapped_view


@ensure_csrf_cookie
@cyberpanel_login_required
@require_http_methods(["GET"])
def main_view(request):
    """Main Redis Manager page: status, controls, info, settings."""
    try:
        mailUtilities.checkHome()
        status_key, status_msg = utils.get_service_status()
        info_text, info_error = utils.get_redis_info()
        config_dict, config_path, config_error, config_read_warning = utils.get_editable_config()
        if not config_dict and config_error:
            config_dict = utils.get_editable_config_form_defaults()
        custom_path = utils.get_custom_config_path() or ''
        config_defaults = utils.get_editable_config_defaults()
        context = {
            'title': 'Redis Manager',
            'plugin_name': 'Redis Manager',
            'version': '1.0.0',
            'is_paid': False,
            'installed': utils.is_installed(),
            'status_key': status_key,
            'status_msg': status_msg,
            'info_text': info_text or '',
            'info_error': info_error or '',
            'redis_config': config_dict,
            'redis_config_path': config_path or '',
            'redis_config_error': config_error or '',
            'redis_config_read_warning': config_read_warning or '',
            'redis_custom_config_path': custom_path,
            'redis_config_defaults': config_defaults,
            'redis_config_defaults_json': json.dumps(config_defaults),
        }
        proc = httpProc(request, 'redisManager/index.html', context, 'admin')
        return proc.render()
    except Exception as e:
        from plogical.CyberCPLogFileWriter import CyberCPLogFileWriter as logging

        logging.writeToFile('Redis Manager main_view error: %s' % str(e))
        return HttpResponse('Internal server error', status=500)


@cyberpanel_login_required
@require_http_methods(["POST"])
def api_control(request):
    """API: start, stop, restart Redis."""
    try:
        data = json.loads(request.body) if request.body else {}
        action = (data.get('action') or '').strip().lower()
        if action not in ('start', 'stop', 'restart'):
            return JsonResponse({'success': False, 'error': 'Invalid action'}, status=400)
        ok, msg = utils.service_control(action)
        return JsonResponse({'success': ok, 'message': msg})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return _redis_json_server_error(request, 'Redis Manager api_control error', e)


@cyberpanel_login_required
@require_http_methods(["POST"])
def api_flush(request):
    """API: FLUSHALL Redis."""
    try:
        ok, msg = utils.redis_flush_all()
        return JsonResponse({'success': ok, 'message': msg})
    except Exception as e:
        return _redis_json_server_error(request, 'Redis Manager api_flush error', e)


@cyberpanel_login_required
@require_http_methods(["GET"])
def api_config(request):
    """API: get Redis editable config (JSON)."""
    try:
        config_dict, config_path, config_error, _ = utils.get_editable_config()
        if config_error:
            return JsonResponse({'success': False, 'error': config_error}, status=404)
        return JsonResponse({'success': True, 'config': config_dict})
    except Exception as e:
        return _redis_json_server_error(request, 'Redis Manager api_config error', e)


@cyberpanel_login_required
@require_http_methods(["POST"])
def api_save_config(request):
    """API: save Redis config (JSON body: { key: value, ... })."""
    try:
        if not utils.is_installed():
            return JsonResponse({'success': False, 'error': 'Redis is not installed.'}, status=400)
        data = json.loads(request.body) if request.body else {}
        if not isinstance(data, dict):
            return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
        ok, msg = utils.save_redis_config(data)
        return JsonResponse({'success': ok, 'message': msg})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return _redis_json_server_error(request, 'Redis Manager api_save_config error', e)


@cyberpanel_login_required
@require_http_methods(["GET"])
def api_detect_config(request):
    """API: auto-detect Redis config path from systemd / fallbacks. Returns path or error."""
    try:
        path = utils.detect_redis_config_path()
        if path:
            return JsonResponse({'success': True, 'path': path})
        return JsonResponse({
            'success': False,
            'error': 'Could not detect config. Checked: running process, systemd, paths (%s), and find in /etc, /usr/local, /opt, /var. Set the path manually if Redis uses a custom location.' % ', '.join(utils.REDIS_CONF_PATHS)
        }, status=404)
    except Exception as e:
        return _redis_json_server_error(request, 'Redis Manager api_detect_config error', e)


@cyberpanel_login_required
@require_http_methods(["POST"])
def api_save_config_path(request):
    """API: save custom Redis config path (JSON body: { path: "/etc/redis.conf" }). Empty path clears."""
    try:
        data = json.loads(request.body) if request.body else {}
        path = (data.get('path') or '').strip() if isinstance(data, dict) else ''
        ok, msg = utils.set_custom_config_path(path)
        return JsonResponse({'success': ok, 'message': msg})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return _redis_json_server_error(request, 'Redis Manager api_save_config_path error', e)


@cyberpanel_login_required
@require_http_methods(["POST"])
def api_fix_permissions(request):
    """API: fix permissions on Redis config file so the panel can read it (chmod 644)."""
    try:
        path = utils.get_redis_config_path()
        if not path:
            return JsonResponse({'success': False, 'error': 'Redis config path not set or not found.'}, status=400)
        ok, msg = utils.fix_redis_config_permissions(path)
        return JsonResponse({'success': ok, 'message': msg})
    except Exception as e:
        return _redis_json_server_error(request, 'Redis Manager api_fix_permissions error', e)
