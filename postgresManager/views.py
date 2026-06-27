# -*- coding: utf-8 -*-
import json
import traceback
from functools import wraps

from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from plogical.CyberCPLogFileWriter import CyberCPLogFileWriter as logging
from plogical.httpProc import httpProc

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


def _json(data, status=200):
    return JsonResponse(data, status=status, json_dumps_params={'ensure_ascii': False})


def _body(request):
    return json.loads(request.body.decode('utf-8') or '{}') if request.body else {}


@ensure_csrf_cookie
@cyberpanel_login_required
@require_http_methods(['GET'])
def main_view(request):
    try:
        try:
            from plogical.mailUtilities import mailUtilities
            mailUtilities.checkHome()
        except Exception:
            pass
        status_key, status_msg = utils.get_service_status()
        context = {
            'title': 'PostgreSQL Manager',
            'plugin_name': 'PostgreSQL Manager',
            'version': '1.0.0',
            'is_paid': False,
            'installed': utils.is_installed(),
            'status_key': status_key,
            'status_msg': status_msg,
            'postgres_version': utils.postgres_version(),
            'listen_addresses': utils.get_listen_addresses(),
        }
        context.update(utils.admin_context(request))
        proc = httpProc(request, 'postgresManager/index.html', context, 'admin')
        response = proc.render()
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        return response
    except Exception as exc:
        logging.writeToFile('postgresManager main_view error: %s' % str(exc))
        logging.writeToFile(traceback.format_exc())
        return HttpResponse('PostgreSQL Manager error', status=500)


@cyberpanel_login_required
@csrf_exempt
@require_http_methods(['POST'])
def api_control(request):
    try:
        data = _body(request)
        action = (data.get('action') or '').strip().lower()
        ok, msg = utils.service_control(action)
        return _json({'success': ok, 'message': msg if ok else None, 'error': None if ok else msg}, 200 if ok else 400)
    except ValueError:
        return _json({'success': False, 'error': 'Invalid JSON.'}, 400)
    except Exception as exc:
        logging.writeToFile('postgresManager api_control error: %s' % str(exc))
        return _json({'success': False, 'error': 'Internal server error.'}, 500)


@cyberpanel_login_required
@csrf_exempt
@require_http_methods(['POST'])
def api_init_admin(request):
    try:
        if not utils.is_installed():
            return _json({'success': False, 'error': 'PostgreSQL is not installed. Run this plugin install.sh first.'}, 400)
        ok, msg = utils.ensure_admin_credentials()
        data = {'success': ok, 'message': msg if ok else None, 'error': None if ok else msg}
        data.update(utils.admin_context(request))
        return _json(data, 200 if ok else 400)
    except Exception as exc:
        logging.writeToFile('postgresManager api_init_admin error: %s' % str(exc))
        return _json({'success': False, 'error': 'Internal server error.'}, 500)


@cyberpanel_login_required
@require_http_methods(['GET'])
def api_websites(request):
    try:
        return _json({'success': True, 'websites': utils.list_websites_for_user(request.session['userID'])})
    except Exception as exc:
        logging.writeToFile('postgresManager api_websites error: %s' % str(exc))
        return _json({'success': False, 'error': 'Internal server error.'}, 500)


@cyberpanel_login_required
@require_http_methods(['GET'])
def api_databases(request):
    try:
        domain = (request.GET.get('domain') or '').strip() or None
        return _json({'success': True, 'databases': utils.list_databases(request.session['userID'], domain)})
    except Exception as exc:
        logging.writeToFile('postgresManager api_databases error: %s' % str(exc))
        return _json({'success': False, 'error': 'Internal server error.'}, 500)


@cyberpanel_login_required
@csrf_exempt
@require_http_methods(['POST'])
def api_create_database(request):
    try:
        data = _body(request)
        record = utils.create_database(
            request.session['userID'],
            (data.get('domain') or '').strip(),
            data.get('database') or '',
            data.get('username') or '',
            data.get('password') or '',
        )
        return _json({'success': True, 'database': record, 'message': 'Database created.'})
    except ValueError as exc:
        return _json({'success': False, 'error': str(exc)}, 400)
    except PermissionError as exc:
        return _json({'success': False, 'error': str(exc)}, 403)
    except Exception as exc:
        logging.writeToFile('postgresManager api_create_database error: %s' % str(exc))
        return _json({'success': False, 'error': str(exc)}, 500)


@cyberpanel_login_required
@csrf_exempt
@require_http_methods(['POST'])
def api_change_password(request):
    try:
        data = _body(request)
        record = utils.change_database_password(
            request.session['userID'],
            data.get('database') or '',
            data.get('username') or '',
            data.get('password') or '',
        )
        return _json({'success': True, 'database': record, 'message': 'Password changed.'})
    except ValueError as exc:
        return _json({'success': False, 'error': str(exc)}, 400)
    except PermissionError as exc:
        return _json({'success': False, 'error': str(exc)}, 403)
    except Exception as exc:
        logging.writeToFile('postgresManager api_change_password error: %s' % str(exc))
        return _json({'success': False, 'error': str(exc)}, 500)


@cyberpanel_login_required
@csrf_exempt
@require_http_methods(['POST'])
def api_delete_database(request):
    try:
        data = _body(request)
        record = utils.delete_database(
            request.session['userID'],
            data.get('database') or '',
            data.get('username') or '',
        )
        return _json({'success': True, 'database': record, 'message': 'Database deleted.'})
    except ValueError as exc:
        return _json({'success': False, 'error': str(exc)}, 400)
    except PermissionError as exc:
        return _json({'success': False, 'error': str(exc)}, 403)
    except Exception as exc:
        logging.writeToFile('postgresManager api_delete_database error: %s' % str(exc))
        return _json({'success': False, 'error': str(exc)}, 500)
