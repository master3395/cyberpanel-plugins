# -*- coding: utf-8 -*-
"""
One-time phpMyAdmin launch URLs (POST into CyberPanel phpmyadminsignin.php signon flow).
"""
import html
import json
import secrets
import os
from datetime import timedelta
from functools import wraps

from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from plogical.CyberCPLogFileWriter import CyberCPLogFileWriter as logging

from . import acl_helpers
from . import crypto_util
from .models import LimitedPhpmyAdminGrant, PmaLaunchToken

SIGNON_PATH = '/phpmyadmin/phpmyadminsignin.php'
POLICY_PATHS = (
    '/usr/local/CyberCP/pluginState/limited_phpmyadmin_policy.json',
    '/var/lib/cyberpanel-panelstate/limited_phpmyadmin_policy.json',
    '/etc/cyberpanel/limited_phpmyadmin_policy.json',
)


def _json(data, status=200):
    return JsonResponse(data, status=status, json_dumps_params={'ensure_ascii': False})


def _cyberpanel_api_login_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        try:
            request.session['userID']
        except KeyError:
            return _json(
                {'success': False, 'error': 'Session expired. Reload the page and sign in again.'},
                401,
            )
        return view_func(request, *args, **kwargs)

    return _wrapped_view


def _catch_json_api_errors(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        try:
            return view_func(request, *args, **kwargs)
        except Exception as exc:
            logging.writeToFile(
                'limitedPhpmyAdmin %s: %s' % (getattr(view_func, '__name__', 'pma_launch'), str(exc))
            )
            return _json(
                {
                    'success': False,
                    'error': 'Unexpected server error. Check CyberPanel logs.',
                },
                500,
            )

    return _wrapped_view


def _require_api_session(request):
    triplet = acl_helpers.get_session_admin_acl(request)
    if triplet[0] is None:
        return None
    return triplet


def _purge_expired_tokens():
    try:
        PmaLaunchToken.objects.filter(expires_at__lt=timezone.now()).delete()
    except Exception as exc:
        logging.writeToFile('limitedPhpmyAdmin purge launch tokens: %s' % str(exc))


def _read_policy_dict():
    for path in POLICY_PATHS:
        try:
            if not os.path.exists(path):
                continue
            with open(path, 'r') as f:
                data = json.load(f)
            if isinstance(data, dict):
                return data
        except Exception as exc:
            logging.writeToFile('limitedPhpmyAdmin policy read %s: %s' % (path, str(exc)))
    return {}


def _is_strict_mode_enabled():
    data = _read_policy_dict()
    if data:
        return bool(data.get('strict_mode', True))
    return True


def _launch_ttl_and_single_use():
    """TTL in hours (1–720) and whether consuming the link invalidates it."""
    data = _read_policy_dict()
    ttl = 24
    single_use = True
    if data:
        try:
            ttl = int(data.get('pma_launch_ttl_hours', 24))
        except (TypeError, ValueError):
            ttl = 24
        ttl = max(1, min(720, ttl))
        single_use = bool(data.get('pma_launch_single_use', True))
    return ttl, single_use


@_cyberpanel_api_login_required
@csrf_exempt
@require_http_methods(['POST'])
@_catch_json_api_errors
def api_create_pma_launch_link(request):
    sess = _require_api_session(request)
    if not sess:
        return _json({'success': False, 'error': 'Unauthorized'}, 401)
    _, admin, acl = sess
    try:
        body = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return _json({'success': False, 'error': 'Invalid JSON'}, 400)
    try:
        gid = int(body.get('grant_id'))
    except (TypeError, ValueError):
        return _json({'success': False, 'error': 'Invalid grant_id'}, 400)
    try:
        g = LimitedPhpmyAdminGrant.objects.get(pk=gid)
    except LimitedPhpmyAdminGrant.DoesNotExist:
        return _json({'success': False, 'error': 'Not found'}, 404)
    if acl_helpers.resolve_owned_website(admin, acl, g.website_id) is None:
        return _json({'success': False, 'error': 'Forbidden'}, 403)
    if not g.enabled:
        return _json({'success': False, 'error': 'Grant is disabled; enable it first.'}, 400)
    try:
        crypto_util.decrypt_password(g.password_encrypted)
    except Exception:
        return _json({'success': False, 'error': 'Could not read stored password; rotate password first.'}, 500)

    _purge_expired_tokens()
    ttl_hours, single_use = _launch_ttl_and_single_use()
    raw = secrets.token_urlsafe(32)
    exp = timezone.now() + timedelta(hours=ttl_hours)
    PmaLaunchToken.objects.create(grant=g, token=raw, expires_at=exp)

    rel = reverse('limitedPhpmyAdmin:pma_launch', kwargs={'token': raw})
    url = request.build_absolute_uri(rel)
    use_msg = (
        'Single-use; expires in %s hours. Send only over HTTPS.'
        if single_use
        else 'Multi-use until expiry; expires in %s hours. Send only over HTTPS (weaker than single-use).'
    ) % ttl_hours
    return _json(
        {
            'success': True,
            'url': url,
            'expires_at': exp.isoformat(),
            'ttl_hours': ttl_hours,
            'single_use': single_use,
            'message': use_msg,
        }
    )


@require_http_methods(['GET'])
def pma_launch(request, token):
    """
    Public endpoint: consuming the token shows an auto-submitting POST form to phpMyAdmin signon.
    """
    if not token or len(token) > 70:
        return HttpResponse('Invalid link.', status=400, content_type='text/plain; charset=utf-8')
    try:
        row = PmaLaunchToken.objects.select_related('grant').get(token=token)
    except PmaLaunchToken.DoesNotExist:
        return HttpResponse('This link is invalid or has expired.', status=410, content_type='text/plain; charset=utf-8')

    now = timezone.now()
    if row.expires_at < now:
        return HttpResponse('This link has expired.', status=410, content_type='text/plain; charset=utf-8')
    _ttl_ignore, single_use = _launch_ttl_and_single_use()
    if single_use and row.used_at is not None:
        return HttpResponse('This link has already been used.', status=410, content_type='text/plain; charset=utf-8')

    g = row.grant
    if not g.enabled:
        return HttpResponse('This grant is disabled.', status=403, content_type='text/plain; charset=utf-8')

    try:
        plain = crypto_util.decrypt_password(g.password_encrypted)
    except Exception as exc:
        logging.writeToFile('limitedPhpmyAdmin pma_launch decrypt: %s' % str(exc))
        return HttpResponse('Could not unlock credentials.', status=500, content_type='text/plain; charset=utf-8')

    if single_use:
        row.used_at = now
        row.save(update_fields=['used_at'])

    action = request.build_absolute_uri(SIGNON_PATH)

    def esc_attr(val):
        return html.escape(val or '', quote=True)

    body = (
        '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="robots" content="noindex,nofollow">'
        '<title>phpMyAdmin</title></head><body>'
        '<p>Signing in to phpMyAdmin…</p>'
        '<form id="pma" method="post" action="'
        + esc_attr(action)
        + '"><input type="hidden" name="username" value="'
        + esc_attr(g.mysql_username)
        + '"><input type="hidden" name="password" value="'
        + esc_attr(plain)
        + '"><input type="hidden" name="lpma_strict" value="'
        + ('1' if _is_strict_mode_enabled() else '0')
        + '"></form>'
        '<script>document.getElementById("pma").submit();</script>'
        '<noscript><button type="submit" form="pma">Continue to phpMyAdmin</button></noscript>'
        '</body></html>'
    )

    return HttpResponse(body, content_type='text/html; charset=utf-8')
