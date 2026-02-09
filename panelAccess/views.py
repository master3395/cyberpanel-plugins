# -*- coding: utf-8 -*-
"""
Panel Access settings: configure custom panel domain(s) for CSRF when
the panel is behind a reverse proxy (e.g. https://panel.example.com -> IP:2087).
"""
from django.shortcuts import redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils.translation import gettext as _
from loginSystem.views import loadLoginPage
from plogical.httpProc import httpProc
from plogical.mailUtilities import mailUtilities
from .apps import get_panel_csrf_origins_file, read_panel_csrf_origins
import os
import subprocess


def _ensure_origins_dir():
    """Ensure directory for panel_csrf_origins.conf exists."""
    path = get_panel_csrf_origins_file()
    d = os.path.dirname(path)
    if d and not os.path.isdir(d):
        try:
            os.makedirs(d, mode=0o755)
        except (OSError, IOError):
            pass


@require_http_methods(['GET'])
def settings_page(request):
    """Show Panel Access settings page with current custom domains."""
    try:
        request.session['userID']
    except KeyError:
        return redirect(loadLoginPage)
    mailUtilities.checkHome()
    origins = read_panel_csrf_origins()
    data = {
        'origins_text': '\n'.join(origins),
        'config_path': get_panel_csrf_origins_file(),
    }
    proc = httpProc(request, 'panelAccess/settings.html', data, 'admin')
    return proc.render()


@require_http_methods(['POST'])
def save_origins(request):
    """Save custom panel origins (one per line). Admin only. Returns JSON."""
    try:
        request.session['userID']
    except KeyError:
        return redirect(loadLoginPage)
    try:
        from loginSystem.models import Administrator
        from plogical.acl import ACLManager
        user_id = request.session['userID']
        current_acl = ACLManager.loadedACL(user_id)
        if not current_acl.get('admin'):
            return JsonResponse({
                'save': 0,
                'error_message': _('Only administrators can change Panel Access settings.'),
            }, status=403)
    except Exception:
        return JsonResponse({
            'save': 0,
            'error_message': _('Authorization check failed.'),
        }, status=500)
    origins_raw = request.POST.get('origins', '').strip()
    lines = [ln.strip() for ln in origins_raw.splitlines() if ln.strip() and not ln.strip().startswith('#')]
    path = get_panel_csrf_origins_file()
    _ensure_origins_dir()
    try:
        with open(path, 'w') as f:
            f.write('# Custom panel domain(s) for CSRF (one origin per line)\n')
            for line in lines:
                f.write(line + '\n')
        try:
            os.chmod(path, 0o600)
        except (OSError, IOError):
            pass
    except (OSError, IOError) as e:
        return JsonResponse({
            'save': 0,
            'error_message': _('Could not write config file: %s') % str(e),
        })

    message = _('Custom domains saved. Restart the CyberPanel backend (e.g. systemctl restart lscpd) for CSRF to take effect.')
    proxy_results = []

    setup_ols = request.POST.get('setup_ols_proxy', '').strip().lower() in ('1', 'true', 'yes', 'on')
    if setup_ols and lines:
        try:
            from .ols_proxy import setup_panel_proxy_vhost, domain_from_origin
        except ImportError:
            pass
        else:
            seen = set()
            for origin in lines:
                domain = domain_from_origin(origin)
                if not domain or domain in seen:
                    continue
                seen.add(domain)
                ok, msg = setup_panel_proxy_vhost(domain)
                proxy_results.append({'domain': domain, 'success': ok, 'message': msg})
            if proxy_results:
                parts = [message]
                for r in proxy_results:
                    parts.append('{}: {}'.format(r['domain'], r['message']))
                message = ' '.join(parts)

    # Restart lscpd so Django loads the new CSRF origins
    restart_ok = False
    restart_error = None
    try:
        r = subprocess.run(
            ['systemctl', 'restart', 'lscpd'],
            capture_output=True,
            text=True,
            timeout=15,
        )
        restart_ok = (r.returncode == 0)
        if not restart_ok and r.stderr:
            restart_error = r.stderr.strip() or r.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError) as e:
        restart_error = str(e)

    if restart_ok:
        message = _('Custom domains saved. CyberPanel backend (lscpd) restarted; CSRF changes are active.')
        if proxy_results:
            message = message + ' ' + ' '.join('{}: {}.'.format(r['domain'], r['message']) for r in proxy_results)
    else:
        message = _('Custom domains saved. Restart the CyberPanel backend manually (systemctl restart lscpd) for CSRF to take effect.')
        if restart_error:
            message = message + ' ' + _('Restart failed: %s') % restart_error
        if proxy_results:
            message = message + ' ' + ' '.join('{}: {}.'.format(r['domain'], r['message']) for r in proxy_results)

    return JsonResponse({
        'save': 1,
        'message': message,
        'proxy_results': proxy_results,
        'lscpd_restarted': restart_ok,
    })
