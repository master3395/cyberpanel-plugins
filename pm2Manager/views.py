# -*- coding: utf-8 -*-
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from plogical.mailUtilities import mailUtilities
from plogical.httpProc import httpProc
from plogical.plugin_acl import require_manage_plugins_api
from plogical.CyberCPLogFileWriter import CyberCPLogFileWriter as logging
from functools import wraps
import json
from .utils import (
    get_pm2_list, get_pm2_info, get_pm2_logs, get_pm2_status,
    start_pm2_app, stop_pm2_app, restart_pm2_app, delete_pm2_app, add_pm2_app,
    format_pm2_process
)

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
def dashboard(request):
    """Main PM2 Manager dashboard - pass PM2 status for initial display"""
    mailUtilities.checkHome()
    try:
        pm2_status = get_pm2_status()
    except Exception as e:
        logging.writeToFile(f"PM2 Manager get_pm2_status error: {str(e)}")
        pm2_status = {'installed': False, 'running': False, 'message': str(e)}
    context = {'pm2_status': pm2_status}
    proc = httpProc(request, 'pm2Manager/dashboard.html', context, 'managePlugins')
    response = proc.render()
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

@cyberpanel_login_required
def settings(request):
    """PM2 Manager settings page"""
    mailUtilities.checkHome()
    context = {
        'plugin_name': 'PM2 Manager',
        'version': '1.0.0',
        'status': 'Active'
    }
    proc = httpProc(request, 'pm2Manager/settings.html', context, 'managePlugins')
    return proc.render()

@cyberpanel_login_required
def node_detail(request, app_name):
    """Individual node detail page"""
    mailUtilities.checkHome()
    context = {
        'app_name': app_name
    }
    proc = httpProc(request, 'pm2Manager/node_detail.html', context, 'managePlugins')
    return proc.render()

# API Endpoints

@cyberpanel_login_required
@require_manage_plugins_api
@csrf_exempt
@require_http_methods(["GET"])
def api_list_apps(request):
    """Get list of all PM2 applications and PM2 status (check status, load active apps)"""
    mailUtilities.checkHome()
    
    try:
        pm2_status = get_pm2_status()
        processes = get_pm2_list()
        formatted_processes = [format_pm2_process(p) for p in processes]
        
        return JsonResponse({
            'success': True,
            'apps': formatted_processes,
            'count': len(formatted_processes),
            'pm2_status': pm2_status
        })
    except Exception as e:
        logging.writeToFile(f"Error listing PM2 apps: {str(e)}")
        try:
            pm2_status = get_pm2_status()
        except Exception:
            pm2_status = {'installed': False, 'running': False, 'message': str(e)}
        return JsonResponse({
            'success': False,
            'error': str(e),
            'pm2_status': pm2_status
        }, status=500)

@cyberpanel_login_required
@require_manage_plugins_api
@csrf_exempt
@require_http_methods(["GET"])
def api_get_info(request, app_name):
    """Get detailed information about a PM2 app. Returns formatted info for the detail page."""
    mailUtilities.checkHome()
    
    try:
        raw = get_pm2_info(app_name)
        if raw is None:
            # Fallback: find app in list (e.g. if "pm2 show" failed but app exists)
            processes = get_pm2_list()
            for proc in processes:
                if proc.get('name') == app_name:
                    return JsonResponse({
                        'success': True,
                        'info': format_pm2_process(proc)
                    })
            return JsonResponse({
                'success': False,
                'error': f'App {app_name} not found'
            }, status=404)
        # Format raw PM2 output so frontend gets status, uptime (seconds), cpu, memory, etc.
        if isinstance(raw, dict) and ('pm2_env' in raw or 'monit' in raw):
            info = format_pm2_process(raw)
        else:
            info = raw
        return JsonResponse({
            'success': True,
            'info': info
        })
    except Exception as e:
        logging.writeToFile(f"Error getting PM2 app info: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@cyberpanel_login_required
@require_manage_plugins_api
@csrf_exempt
@require_http_methods(["GET"])
def api_get_logs(request, app_name):
    """Get logs for a PM2 app"""
    mailUtilities.checkHome()
    
    try:
        lines = int(request.GET.get('lines', 100))
        logs, error_msg = get_pm2_logs(app_name, lines)
        
        if error_msg is not None:
            return JsonResponse({
                'success': False,
                'error': error_msg,
                'logs': []
            })
        
        return JsonResponse({
            'success': True,
            'logs': logs
        })
    except Exception as e:
        logging.writeToFile(f"Error getting PM2 logs: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@cyberpanel_login_required
@require_manage_plugins_api
@csrf_exempt
@require_http_methods(["POST"])
def api_start_app(request, app_name):
    """Start a PM2 application"""
    mailUtilities.checkHome()
    
    try:
        result = start_pm2_app(app_name)
        if result['success']:
            return JsonResponse({
                'success': True,
                'message': f'App {app_name} started successfully'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result.get('error', 'Failed to start app')
            }, status=400)
    except Exception as e:
        logging.writeToFile(f"Error starting PM2 app: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@cyberpanel_login_required
@require_manage_plugins_api
@csrf_exempt
@require_http_methods(["POST"])
def api_stop_app(request, app_name):
    """Stop a PM2 application"""
    mailUtilities.checkHome()
    
    try:
        result = stop_pm2_app(app_name)
        if result['success']:
            return JsonResponse({
                'success': True,
                'message': f'App {app_name} stopped successfully'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result.get('error', 'Failed to stop app')
            }, status=400)
    except Exception as e:
        logging.writeToFile(f"Error stopping PM2 app: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@cyberpanel_login_required
@require_manage_plugins_api
@csrf_exempt
@require_http_methods(["POST"])
def api_restart_app(request, app_name):
    """Restart a PM2 application"""
    mailUtilities.checkHome()
    
    try:
        result = restart_pm2_app(app_name)
        if result['success']:
            return JsonResponse({
                'success': True,
                'message': f'App {app_name} restarted successfully'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result.get('error', 'Failed to restart app')
            }, status=400)
    except Exception as e:
        logging.writeToFile(f"Error restarting PM2 app: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@cyberpanel_login_required
@require_manage_plugins_api
@csrf_exempt
@require_http_methods(["POST"])
def api_delete_app(request, app_name):
    """Delete a PM2 application"""
    mailUtilities.checkHome()
    
    try:
        result = delete_pm2_app(app_name)
        if result['success']:
            return JsonResponse({
                'success': True,
                'message': f'App {app_name} deleted successfully'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result.get('error', 'Failed to delete app')
            }, status=400)
    except Exception as e:
        logging.writeToFile(f"Error deleting PM2 app: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@cyberpanel_login_required
@require_manage_plugins_api
@csrf_exempt
@require_http_methods(["POST"])
def api_add_app(request):
    """Add a new PM2 application"""
    mailUtilities.checkHome()
    
    try:
        data = json.loads(request.body)
        
        name = data.get('name', '').strip()
        script_path = data.get('script_path', '').strip()
        args = data.get('args', '').strip()
        instances = int(data.get('instances', 1))
        exec_mode = data.get('exec_mode', 'fork')
        env_vars = data.get('env_vars', {})
        
        # New parameters
        max_memory_restart = data.get('max_memory_restart', '').strip() or None
        autorestart = data.get('autorestart', True)
        if isinstance(autorestart, str):
            autorestart = autorestart.lower() in ('true', '1', 'yes', 'on')
        cwd = data.get('cwd', '').strip() or None
        interpreter = data.get('interpreter', '').strip() or None
        
        if not name or not script_path:
            return JsonResponse({
                'success': False,
                'error': 'Name and script_path are required'
            }, status=400)
        
        result = add_pm2_app(
            name, script_path, args, instances, exec_mode, env_vars,
            max_memory_restart=max_memory_restart,
            autorestart=autorestart,
            cwd=cwd,
            interpreter=interpreter
        )
        
        if result['success']:
            return JsonResponse({
                'success': True,
                'message': f'App {name} added successfully'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result.get('error', 'Failed to add app')
            }, status=400)
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logging.writeToFile(f"Error adding PM2 app: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@cyberpanel_login_required
@require_manage_plugins_api
@csrf_exempt
@require_http_methods(["GET"])
def api_monitor(request):
    """Get real-time monitoring data for all apps"""
    mailUtilities.checkHome()
    
    try:
        processes = get_pm2_list()
        monitoring_data = []
        
        for process in processes:
            formatted = format_pm2_process(process)
            monitoring_data.append(formatted)
        
        return JsonResponse({
            'success': True,
            'data': monitoring_data,
            'timestamp': int(__import__('time').time())
        })
    except Exception as e:
        logging.writeToFile(f"Error getting PM2 monitor data: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
