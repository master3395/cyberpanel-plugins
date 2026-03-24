# -*- coding: utf-8 -*-
import json
import secrets
import string
import traceback
from functools import wraps

from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from plogical.httpProc import httpProc
from plogical.mailUtilities import mailUtilities
from plogical.CyberCPLogFileWriter import CyberCPLogFileWriter as logging

from . import acl_helpers
from . import crypto_util
from . import mysql_grant
from .models import LimitedPhpmyAdminGrant


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


def cyberpanel_api_login_required(view_func):
    """Like cyberpanel_login_required but return JSON 401 for fetch/XHR (never HTML redirect)."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        try:
            request.session['userID']
        except KeyError:
            return _json(
                {
                    'success': False,
                    'error': 'Session expired. Reload the page and sign in again.',
                },
                401,
            )
        return view_func(request, *args, **kwargs)

    return _wrapped_view


def catch_json_api_errors(view_func):
    """Return JSON 500 instead of Django HTML error pages for plugin API calls."""

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        try:
            return view_func(request, *args, **kwargs)
        except Exception as exc:
            logging.writeToFile(
                'limitedPhpmyAdmin %s: %s' % (getattr(view_func, '__name__', 'api'), str(exc))
            )
            return _json(
                {
                    'success': False,
                    'error': 'Unexpected server error. Check CyberPanel logs and plugin migrations.',
                },
                500,
            )

    return _wrapped_view


def _gen_mysql_username():
    # cpma_ + 10 hex = 15 chars (<= 32)
    return 'cpma_' + secrets.token_hex(5)


def _gen_password(length=24):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def _lpma_url_base(request):
    """
    Stable prefix for API paths, e.g. /plugins/limitedPhpmyAdmin/, even when the
    current URL is .../limitedPhpmyAdmin/settings/.
    Avoids {% url %} / namespace issues that can raise NoReverseMatch on some stacks.
    """
    p = request.path or ''
    marker = 'limitedPhpmyAdmin'
    i = p.find(marker)
    if i < 0:
        return '/plugins/limitedPhpmyAdmin/'
    return p[: i + len(marker)] + '/'


@cyberpanel_login_required
@require_http_methods(['GET'])
def main_view(request):
    try:
        mailUtilities.checkHome()
    except Exception:
        pass
    try:
        user_id, admin, acl = acl_helpers.get_session_admin_acl(request)
        sites = acl_helpers.get_allowed_websites(user_id, acl) if user_id else []
        site_opts = [{'id': s.pk, 'domain': s.domain} for s in sites]
        api_grants_url = _lpma_url_base(request) + 'api/grants/'
        context = {
            'title': 'Limited phpMyAdmin',
            'plugin_name': 'Limited phpMyAdmin',
            'version': '1.1.3',
            'is_paid': False,
            'sites_json': json.dumps(site_opts, ensure_ascii=False),
            'api_grants_url': api_grants_url,
        }
        proc = httpProc(request, 'limitedPhpmyAdmin/index.html', context, 'admin')
        return proc.render()
    except Exception as exc:
        try:
            logging.writeToFile('limitedPhpmyAdmin main_view error: %s' % str(exc))
            logging.writeToFile(traceback.format_exc())
        except Exception:
            pass
        try:
            from django.shortcuts import render

            return render(
                request,
                'baseTemplate/error.html',
                {
                    'error_message': (
                        'Limited phpMyAdmin failed to load. If this persists, check '
                        'CyberPanel logs, run: cd /usr/local/CyberCP && python3 manage.py '
                        'migrate limitedPhpmyAdmin --noinput, then systemctl restart lscpd.'
                    ),
                },
            )
        except Exception:
            return HttpResponse('Limited phpMyAdmin error', status=500)


def _require_api_session(request):
    triplet = acl_helpers.get_session_admin_acl(request)
    if triplet[0] is None:
        return None
    return triplet


@cyberpanel_api_login_required
@csrf_exempt
@require_http_methods(['GET'])
@catch_json_api_errors
def api_list_domains(request):
    sess = _require_api_session(request)
    if not sess:
        return _json({'success': False, 'error': 'Unauthorized'}, 401)
    user_id, admin, acl = sess
    sites = acl_helpers.get_allowed_websites(user_id, acl)
    return _json({'success': True, 'sites': [{'id': s.pk, 'domain': s.domain} for s in sites]})


@cyberpanel_api_login_required
@csrf_exempt
@require_http_methods(['GET'])
@catch_json_api_errors
def api_list_databases(request):
    sess = _require_api_session(request)
    if not sess:
        return _json({'success': False, 'error': 'Unauthorized'}, 401)
    _, admin, acl = sess
    site = acl_helpers.resolve_owned_website(admin, acl, request.GET.get('website_id'))
    if not site:
        return _json({'success': False, 'error': 'Invalid website'}, 400)
    from databases.models import Databases
    dbs = Databases.objects.filter(website=site).order_by('dbName')
    return _json({'success': True, 'databases': [{'dbName': d.dbName} for d in dbs]})


@cyberpanel_api_login_required
@csrf_exempt
@require_http_methods(['GET'])
@catch_json_api_errors
def api_list_ftp(request):
    sess = _require_api_session(request)
    if not sess:
        return _json({'success': False, 'error': 'Unauthorized'}, 401)
    _, admin, acl = sess
    site = acl_helpers.resolve_owned_website(admin, acl, request.GET.get('website_id'))
    if not site:
        return _json({'success': False, 'error': 'Invalid website'}, 400)
    return _json({'success': True, 'ftp_users': acl_helpers.list_ftp_for_website(site)})


@cyberpanel_api_login_required
@csrf_exempt
@require_http_methods(['GET'])
@catch_json_api_errors
def api_list_cpusers(request):
    sess = _require_api_session(request)
    if not sess:
        return _json({'success': False, 'error': 'Unauthorized'}, 401)
    _, admin, acl = sess
    site = acl_helpers.resolve_owned_website(admin, acl, request.GET.get('website_id'))
    if not site:
        return _json({'success': False, 'error': 'Invalid website'}, 400)
    return _json({'success': True, 'cp_users': acl_helpers.list_cpusers_for_website(site)})


def _grant_to_dict(g):
    return {
        'id': g.pk,
        'website_id': g.website_id,
        'domain': g.website.domain,
        'database_name': g.database_name,
        'subject_type': g.subject_type,
        'subject_label': g.subject_label,
        'mysql_username': g.mysql_username,
        'enabled': g.enabled,
        'notes': g.notes or '',
        'created_at': g.created_at.isoformat() if g.created_at else '',
    }


@cyberpanel_api_login_required
@csrf_exempt
@require_http_methods(['GET'])
@catch_json_api_errors
def api_list_grants(request):
    sess = _require_api_session(request)
    if not sess:
        return _json({'success': False, 'error': 'Unauthorized'}, 401)
    user_id, admin, acl = sess
    site = acl_helpers.resolve_owned_website(admin, acl, request.GET.get('website_id'))
    if not site:
        return _json({'success': False, 'error': 'Invalid website'}, 400)
    grants = LimitedPhpmyAdminGrant.objects.filter(website=site)
    return _json({'success': True, 'grants': [_grant_to_dict(g) for g in grants]})


@cyberpanel_api_login_required
@csrf_exempt
@require_http_methods(['POST'])
@catch_json_api_errors
def api_create_grant(request):
    sess = _require_api_session(request)
    if not sess:
        return _json({'success': False, 'error': 'Unauthorized'}, 401)
    _, admin, acl = sess
    try:
        body = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return _json({'success': False, 'error': 'Invalid JSON'}, 400)
    site = acl_helpers.resolve_owned_website(admin, acl, body.get('website_id'))
    if not site:
        return _json({'success': False, 'error': 'Invalid website'}, 400)
    db_name = (body.get('database_name') or '').strip()
    if not acl_helpers.database_on_website(site, db_name):
        return _json({'success': False, 'error': 'Database not found for this website'}, 400)
    st = (body.get('subject_type') or '').strip()
    if st == LimitedPhpmyAdminGrant.SUBJECT_FTP:
        fu = acl_helpers.resolve_ftp_user(site, body.get('ftp_user_id'))
        if not fu:
            return _json({'success': False, 'error': 'Invalid FTP user'}, 400)
        label = fu.user
        ftp_id = fu.pk
        adm_id = None
    elif st == LimitedPhpmyAdminGrant.SUBJECT_CPUSER:
        adm = acl_helpers.resolve_cpuser_for_website(site, body.get('administrator_id'))
        if not adm:
            return _json({'success': False, 'error': 'Invalid CyberPanel user for this website'}, 400)
        label = adm.userName
        ftp_id = None
        adm_id = adm.pk
    else:
        return _json({'success': False, 'error': 'subject_type must be ftp or cpuser'}, 400)
    notes = (body.get('notes') or '')[:2000]
    mysql_user = _gen_mysql_username()
    if LimitedPhpmyAdminGrant.objects.filter(mysql_username=mysql_user).exists():
        mysql_user = _gen_mysql_username()
    plain_pw = _gen_password()
    ok, err = mysql_grant.provision_mysql_user(db_name, mysql_user, plain_pw)
    if not ok:
        logging.writeToFile('limitedPhpmyAdmin api_create_grant MySQL: %s' % (err or ''))
        return _json({'success': False, 'error': err or 'MySQL error'}, 500)
    try:
        g = LimitedPhpmyAdminGrant(
            website=site,
            database_name=db_name,
            subject_type=st,
            subject_label=label,
            ftp_user_id=ftp_id,
            administrator_id=adm_id,
            mysql_username=mysql_user,
            password_encrypted=crypto_util.encrypt_password(plain_pw),
            enabled=True,
            notes=notes,
        )
        g.save()
    except RuntimeError as exc:
        mysql_grant.drop_mysql_user(mysql_user)
        logging.writeToFile('limitedPhpmyAdmin api_create_grant: %s' % str(exc))
        return _json({'success': False, 'error': str(exc)}, 500)
    except Exception as exc:
        mysql_grant.drop_mysql_user(mysql_user)
        logging.writeToFile('limitedPhpmyAdmin api_create_grant save: %s' % str(exc))
        return _json({'success': False, 'error': 'Failed to save grant'}, 500)
    return _json({
        'success': True,
        'grant': _grant_to_dict(g),
        'password': plain_pw,
        'message': 'Store this password securely; it is not shown again unless you rotate.',
    })


@cyberpanel_api_login_required
@csrf_exempt
@require_http_methods(['POST'])
@catch_json_api_errors
def api_disable_grant(request):
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
    ok, err = mysql_grant.revoke_database_privileges(g.database_name, g.mysql_username)
    if not ok:
        return _json({'success': False, 'error': err or 'Revoke failed'}, 500)
    g.enabled = False
    g.save(update_fields=['enabled', 'updated_at'])
    return _json({'success': True, 'grant': _grant_to_dict(g)})


@cyberpanel_api_login_required
@csrf_exempt
@require_http_methods(['POST'])
@catch_json_api_errors
def api_enable_grant(request):
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
    try:
        plain = crypto_util.decrypt_password(g.password_encrypted)
    except Exception:
        return _json({'success': False, 'error': 'Could not decrypt stored password; rotate password.'}, 500)
    ok, err = mysql_grant.grant_database_only(g.database_name, g.mysql_username, plain)
    if not ok:
        return _json({'success': False, 'error': err or 'Grant failed'}, 500)
    g.enabled = True
    g.save(update_fields=['enabled', 'updated_at'])
    return _json({'success': True, 'grant': _grant_to_dict(g)})


@cyberpanel_api_login_required
@csrf_exempt
@require_http_methods(['POST'])
@catch_json_api_errors
def api_delete_grant(request):
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
    mysql_grant.revoke_database_privileges(g.database_name, g.mysql_username)
    mysql_grant.drop_mysql_user(g.mysql_username)
    g.delete()
    return _json({'success': True})


@cyberpanel_api_login_required
@csrf_exempt
@require_http_methods(['POST'])
@catch_json_api_errors
def api_rotate_password(request):
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
    plain_pw = _gen_password()
    ok, err = mysql_grant.change_mysql_password(g.mysql_username, plain_pw)
    if not ok:
        return _json({'success': False, 'error': err or 'Password change failed'}, 500)
    g.password_encrypted = crypto_util.encrypt_password(plain_pw)
    g.save(update_fields=['password_encrypted', 'updated_at'])
    return _json({
        'success': True,
        'password': plain_pw,
        'grant': _grant_to_dict(g),
        'message': 'New password applied. Store it securely.',
    })


@cyberpanel_api_login_required
@csrf_exempt
@require_http_methods(['POST'])
@catch_json_api_errors
def api_change_database(request):
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
    new_db = (body.get('database_name') or '').strip()
    try:
        g = LimitedPhpmyAdminGrant.objects.get(pk=gid)
    except LimitedPhpmyAdminGrant.DoesNotExist:
        return _json({'success': False, 'error': 'Not found'}, 404)
    site = acl_helpers.resolve_owned_website(admin, acl, g.website_id)
    if site is None:
        return _json({'success': False, 'error': 'Forbidden'}, 403)
    if not acl_helpers.database_on_website(site, new_db):
        return _json({'success': False, 'error': 'Database not found for this website'}, 400)
    if new_db == g.database_name:
        return _json({'success': True, 'grant': _grant_to_dict(g)})
    try:
        plain = crypto_util.decrypt_password(g.password_encrypted)
    except Exception:
        return _json({'success': False, 'error': 'Could not decrypt password'}, 500)
    ok, err = mysql_grant.change_database_for_user(g.database_name, new_db, g.mysql_username, plain)
    if not ok:
        return _json({'success': False, 'error': err or 'Failed to change database'}, 500)
    g.database_name = new_db
    g.save(update_fields=['database_name', 'updated_at'])
    return _json({'success': True, 'grant': _grant_to_dict(g)})


@cyberpanel_api_login_required
@csrf_exempt
@require_http_methods(['POST'])
@catch_json_api_errors
def api_update_notes(request):
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
    g.notes = (body.get('notes') or '')[:2000]
    g.save(update_fields=['notes', 'updated_at'])
    return _json({'success': True, 'grant': _grant_to_dict(g)})
