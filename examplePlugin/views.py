from django.shortcuts import render, HttpResponse, redirect
from plogical.mailUtilities import mailUtilities
from plogical.httpProc import httpProc
from functools import wraps


# Create your views here.

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
def examplePlugin(request):
    """Main view for example plugin"""
    mailUtilities.checkHome()
    
    context = {
        'plugin_name': 'Example Plugin',
        'version': '1.0.0',
        'status': 'Active',
        'description': 'This is an example plugin demonstrating CyberPanel plugin structure.'
    }
    
    proc = httpProc(request, 'examplePlugin/examplePlugin.html', context, 'admin')
    return proc.render()

@cyberpanel_login_required
def settings_view(request):
    """Settings view for example plugin"""
    mailUtilities.checkHome()
    
    context = {
        'plugin_name': 'Example Plugin',
        'version': '1.0.0',
        'status': 'Active',
        'plugin_status': 'Active',
        'description': 'Configure your example plugin settings'
    }
    
    proc = httpProc(request, 'examplePlugin/settings.html', context, 'admin')
    return proc.render()
