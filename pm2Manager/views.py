# -*- coding: utf-8 -*-
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from plogical.mailUtilities import mailUtilities
from plogical.httpProc import httpProc
from plogical.CyberCPLogFileWriter import CyberCPLogFileWriter as logging
import json
from .utils import (
    get_pm2_list, get_pm2_info, get_pm2_logs,
    start_pm2_app, stop_pm2_app, restart_pm2_app, delete_pm2_app, add_pm2_app,
    format_pm2_process
)

def dashboard(request):
    """Main PM2 Manager dashboard"""
    mailUtilities.checkHome()
    proc = httpProc(request, 'pm2Manager/dashboard.html', {}, 'admin')
    return proc.render()

def settings(request):
    """PM2 Manager settings page"""
    mailUtilities.checkHome()
    proc = httpProc(request, 'pm2Manager/settings.html', {}, 'admin')
    return proc.render()

def node_detail(request, app_name):
    """Individual node detail page"""
    mailUtilities.checkHome()
    context = {
        'app_name': app_name
    }
    proc = httpProc(request, 'pm2Manager/node_detail.html', context, 'admin')
    return proc.render()

# API Endpoints

@csrf_exempt
@require_http_methods(["GET"])
def api_list_apps(request):
    """Get list of all PM2 applications"""
    mailUtilities.checkHome()
    
    try:
        processes = get_pm2_list()
        formatted_processes = [format_pm2_process(p) for p in processes]
        
        return JsonResponse({
            'success': True,
            'apps': formatted_processes,
            'count': len(formatted_processes)
        })
    except Exception as e:
        logging.writeToFile(f"Error listing PM2 apps: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def api_get_info(request, app_name):
    """Get detailed information about a PM2 app"""
    mailUtilities.checkHome()
    
    try:
        info = get_pm2_info(app_name)
        if info is None:
            return JsonResponse({
                'success': False,
                'error': f'App {app_name} not found'
            }, status=404)
        
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

@csrf_exempt
@require_http_methods(["GET"])
def api_get_logs(request, app_name):
    """Get logs for a PM2 app"""
    mailUtilities.checkHome()
    
    try:
        lines = int(request.GET.get('lines', 100))
        logs = get_pm2_logs(app_name, lines)
        
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
        
        if not name or not script_path:
            return JsonResponse({
                'success': False,
                'error': 'Name and script_path are required'
            }, status=400)
        
        result = add_pm2_app(name, script_path, args, instances, exec_mode, env_vars)
        
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
            monitoring_data.append({
                'name': formatted['name'],
                'status': formatted['status'],
                'cpu': formatted['cpu'],
                'memory': formatted['memory'],
                'uptime': formatted['uptime'],
                'restarts': formatted['restarts'],
                'pid': formatted['pid'],
                'pm_id': formatted['pm_id']
            })
        
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
