from django.shortcuts import render, redirect
from django.http import JsonResponse
from plogical.mailUtilities import mailUtilities
from plogical.httpProc import httpProc
from functools import wraps

def cyberpanel_login_required(view_func):
    """
    Custom decorator that checks for CyberPanel session userID
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        try:
            userID = request.session['userID']
            # User is authenticated via CyberPanel session
            return view_func(request, *args, **kwargs)
        except KeyError:
            # Not logged in, redirect to login
            from loginSystem.views import loadLoginPage
            return redirect(loadLoginPage)
    return _wrapped_view

@cyberpanel_login_required
def test_plugin_view(request):
    """
    Main view for the test plugin
    """
    mailUtilities.checkHome()
    context = {
        'plugin_name': 'Test Plugin',
        'version': '1.0.0',
        'description': 'A simple test plugin for CyberPanel'
    }
    proc = httpProc(request, 'testPlugin/index.html', context, 'admin')
    return proc.render()

@cyberpanel_login_required
def plugin_info_view(request):
    """
    API endpoint for plugin information
    """
    return JsonResponse({
        'plugin_name': 'Test Plugin',
        'version': '1.0.0',
        'status': 'active',
        'description': 'A simple test plugin for CyberPanel testing'
    })

@cyberpanel_login_required
def settings_view(request):
    """
    Settings page for the test plugin
    """
    mailUtilities.checkHome()
    context = {
        'plugin_name': 'Test Plugin',
        'version': '1.0.0',
        'description': 'A simple test plugin for CyberPanel'
    }
    proc = httpProc(request, 'testPlugin/settings.html', context, 'admin')
    return proc.render()
