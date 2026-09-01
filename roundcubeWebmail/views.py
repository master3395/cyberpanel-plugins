# -*- coding: utf-8 -*-
"""Roundcube Webmail plugin admin settings."""
from django.shortcuts import redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from plogical.httpProc import httpProc
from plogical.plugin_acl import require_manage_plugins_api
from functools import wraps
import json

from . import utils


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


@cyberpanel_login_required
@require_http_methods(["GET"])
def admin_settings(request):
    try:
        from plogical.mailUtilities import mailUtilities
        mailUtilities.checkHome()
    except Exception:
        pass

    status = utils.get_status(request)
    context = {
        'title': 'Roundcube Webmail',
        'plugin_name': 'Roundcube Webmail',
        'version': '1.0.0',
        'is_paid': False,
        'status': status,
    }
    proc = httpProc(request, 'roundcubeWebmail/admin_settings.html', context, 'managePlugins')
    response = proc.render()
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


@cyberpanel_login_required
@require_manage_plugins_api
@csrf_exempt
@require_http_methods(["POST"])
def api_toggle(request):
    try:
        data = json.loads(request.body) if request.body else {}
        enabled = data.get('enabled')
        if enabled is None:
            return JsonResponse({'success': False, 'error': 'enabled is required.'}, status=400)
        utils.set_enabled(bool(enabled))
        status = utils.get_status(request)
        return JsonResponse({
            'success': True,
            'message': 'Roundcube webmail %s.' % ('enabled' if status['enabled'] else 'disabled'),
            'status': status,
        })
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON.'}, status=400)
    except Exception as exc:
        try:
            from plogical.CyberCPLogFileWriter import CyberCPLogFileWriter as logging
            logging.writeToFile('roundcubeWebmail api_toggle: %s' % str(exc))
        except Exception:
            pass
        return JsonResponse({'success': False, 'error': str(exc)}, status=500)


@cyberpanel_login_required
@require_manage_plugins_api
@require_http_methods(["GET"])
def api_status(request):
    try:
        return JsonResponse({'success': True, 'status': utils.get_status(request)})
    except Exception as exc:
        return JsonResponse({'success': False, 'error': str(exc)}, status=500)
