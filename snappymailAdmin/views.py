# -*- coding: utf-8 -*-
"""
SnappyMail Admin Password plugin – change SnappyMail Admin panel password from CyberPanel.
"""
from django.shortcuts import redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.csrf import ensure_csrf_cookie
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
def main_view(request):
    """Main plugin page: form to set SnappyMail Admin password."""
    try:
        from plogical.mailUtilities import mailUtilities
        mailUtilities.checkHome()
    except Exception:
        pass
    available = utils.is_snappymail_available()
    try:
        host = request.get_host()
        scheme = 'https' if request.is_secure() else 'http'
        snappymail_admin_url = '%s://%s/snappymail/?admin' % (scheme, host)
    except Exception:
        snappymail_admin_url = 'https://your-panel:2087/snappymail/?admin'
    context = {
        'title': 'SnappyMail Admin Password',
        'plugin_name': 'SnappyMail Admin Password',
        'version': '1.0.0',
        'is_paid': False,
        'snappymail_available': available,
        'current_admin_login': utils.get_snappymail_admin_login() if available else 'admin',
        'snappymail_admin_url': snappymail_admin_url,
    }
    proc = httpProc(request, 'snappymailAdmin/index.html', context, 'managePlugins')
    response = proc.render()
    # Prevent browser/proxy cache so Admin username field always shows (no stale HTML)
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


@cyberpanel_login_required
@require_manage_plugins_api
@csrf_exempt
@require_http_methods(["POST"])
def api_set_password(request):
    """API: set SnappyMail Admin username and/or password. Body: admin_username (optional), new_password, confirm_password."""
    try:
        data = json.loads(request.body) if request.body else {}
        admin_username = (data.get('admin_username') or '').strip() or None
        new_password = (data.get('new_password') or '').strip()
        confirm_password = (data.get('confirm_password') or '').strip()
        if not new_password:
            return JsonResponse({'success': False, 'error': 'New password is required.'}, status=400)
        if new_password != confirm_password:
            return JsonResponse({'success': False, 'error': 'Passwords do not match.'}, status=400)
        success, message = utils.set_snappymail_admin_password(new_password, admin_login=admin_username)
        if success:
            try:
                host = request.get_host()
                scheme = 'https' if request.is_secure() else 'http'
                login_url = '%s://%s/snappymail/?admin' % (scheme, host)
                message = 'SnappyMail Admin credentials updated. Log in at %s with username "%s" and your new password.' % (login_url, admin_username or 'admin')
            except Exception:
                pass  # keep utils message if get_host fails
            return JsonResponse({'success': True, 'message': message})
        return JsonResponse({'success': False, 'error': message}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON.'}, status=400)
    except Exception as e:
        try:
            from plogical.CyberCPLogFileWriter import CyberCPLogFileWriter as logging
            logging.writeToFile('snappymailAdmin api_set_password: %s' % str(e))
        except Exception:
            pass
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
