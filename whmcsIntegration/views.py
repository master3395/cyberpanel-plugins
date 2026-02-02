# -*- coding: utf-8 -*-
"""
WHMCS Integration - Documentation plugin
Links to the official CyberPanel WHMCS module (runs in WHMCS, not CyberPanel).
Original: https://github.com/jetchirag/cyberpanel-whmcs
Maintained: https://github.com/jesussuarz/cyberpanel-whmcs
"""
from functools import wraps
from plogical.mailUtilities import mailUtilities
from plogical.httpProc import httpProc


def cyberpanel_login_required(view_func):
    """Decorator to check CyberPanel session."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        try:
            request.session['userID']
            return view_func(request, *args, **kwargs)
        except KeyError:
            from loginSystem.views import loadLoginPage
            return loadLoginPage(request)
    return _wrapped_view


@cyberpanel_login_required
def index(request):
    """Render WHMCS integration documentation page."""
    mailUtilities.checkHome()
    context = {
        'plugin_name': 'WHMCS Integration',
        'plugin_version': '1.0.0',
    }
    # function=None allows any logged-in user (admin, reseller, or user)
    proc = httpProc(request, 'whmcsIntegration/index.html', context, None)
    return proc.render()
