# -*- coding: utf-8 -*-
"""
CSP Manager Views
Settings and configuration page for CSP Manager plugin
"""

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from plogical.httpProc import httpProc
from plogical.mailUtilities import mailUtilities
from functools import wraps
import json

from .models import CSPConfig
from .forms import CSPConfigForm


def cyberpanel_login_required(view_func):
    """
    Custom decorator that checks for CyberPanel session userID
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        try:
            userID = request.session['userID']
            return view_func(request, *args, **kwargs)
        except KeyError:
            from loginSystem.views import loadLoginPage
            return redirect(loadLoginPage)
    return _wrapped_view


@cyberpanel_login_required
def main_view(request):
    """Main plugin page - redirects to settings"""
    return redirect('cspManager:settings')


@cyberpanel_login_required
@require_http_methods(["GET", "POST"])
def settings_view(request):
    """Settings page with CSP configuration"""
    try:
        mailUtilities.checkHome()
        
        # Get or create config (may fail if migrations not run)
        try:
            config = CSPConfig.get_config()
        except Exception as db_err:
            from django.db.utils import OperationalError, ProgrammingError
            from django.http import HttpResponse
            from django.core.management import call_command
            from plogical.CyberCPLogFileWriter import CyberCPLogFileWriter as logging
            logging.writeToFile(f"CSP Manager get_config error: {db_err}")
            if isinstance(db_err, (OperationalError, ProgrammingError)):
                try:
                    call_command('migrate', 'cspManager', verbosity=0, interactive=False)
                    config = CSPConfig.get_config()
                except Exception as migrate_err:
                    logging.writeToFile(f"CSP Manager migrate error: {migrate_err}")
                    return HttpResponse(
                        '<div style="padding:20px;font-family:sans-serif;">'
                        '<h2>CSP Manager</h2><p>The database table is missing. Run migrations:</p>'
                        '<pre>cd /usr/local/CyberCP && python3 manage.py migrate cspManager</pre>'
                        '<p>Error: %s</p></div>' % str(db_err),
                        status=503
                    )
            else:
                raise
        
        if request.method == 'POST':
            form = CSPConfigForm(request.POST, instance=config)
            if form.is_valid():
                form.save()
                context = {
                    'title': 'CSP Manager Settings',
                    'plugin_name': 'CSP Manager',
                    'version': '1.0.0',
                    'form': CSPConfigForm(instance=config),
                    'config': config,
                    'success_message': 'CSP settings saved successfully!',
                }
            else:
                context = {
                    'title': 'CSP Manager Settings',
                    'plugin_name': 'CSP Manager',
                    'version': '1.0.0',
                    'form': form,
                    'config': config,
                    'error_message': 'Please correct the errors below.',
                }
        else:
            form = CSPConfigForm(instance=config)
            context = {
                'title': 'CSP Manager Settings',
                'plugin_name': 'CSP Manager',
                'version': '1.0.0',
                'form': form,
                'config': config,
            }
        
        proc = httpProc(request, 'cspManager/settings.html', context, 'admin')
        return proc.render()
        
    except Exception as e:
        from plogical.CyberCPLogFileWriter import CyberCPLogFileWriter as logging
        logging.writeToFile(f"CSP Manager settings error: {str(e)}")
        import traceback
        error_trace = traceback.format_exc()
        logging.writeToFile(f"CSP Manager traceback: {error_trace}")
        from django.http import HttpResponse
        return HttpResponse(f"<div style='padding: 20px;'><h2>Settings Error</h2><p>{str(e)}</p><pre>{error_trace}</pre></div>")


@cyberpanel_login_required
@csrf_exempt
@require_http_methods(["POST"])
def toggle_plugin_csp(request):
    """API endpoint to toggle CSP for a specific plugin"""
    try:
        data = json.loads(request.body)
        plugin_name = data.get('plugin_name', '').strip()
        enabled = data.get('enabled', True)
        
        if not plugin_name:
            return JsonResponse({
                'success': False,
                'error': 'Plugin name is required'
            }, status=400)
        
        config = CSPConfig.get_config()
        config.set_plugin_setting(plugin_name, 'enabled', enabled)
        
        return JsonResponse({
            'success': True,
            'message': f'CSP {"enabled" if enabled else "disabled"} for {plugin_name}',
            'plugin_name': plugin_name,
            'enabled': enabled
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        from plogical.CyberCPLogFileWriter import CyberCPLogFileWriter as logging
        logging.writeToFile(f"CSP Manager toggle error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
