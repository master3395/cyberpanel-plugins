# -*- coding: utf-8 -*-
"""
Google Tag Manager Plugin Views
"""

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from plogical.mailUtilities import mailUtilities
from plogical.httpProc import httpProc
from plogical.CyberCPLogFileWriter import CyberCPLogFileWriter as logging
from plogical.acl import ACLManager
from functools import wraps
import json
import re

from .models import GTMSettings
from .utils import get_user_domains, get_gtm_code_full, get_gtm_for_domain


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
    """
    Main view for Google Tag Manager plugin
    Shows overview of all domains and their GTM status
    """
    mailUtilities.checkHome()
    
    try:
        userID = request.session['userID']
        currentACL = ACLManager.loadedACL(userID)
        
        # Get all user domains
        domains = get_user_domains(userID, currentACL)
        
        # Get GTM settings for all domains
        gtm_settings = {}
        for domain_info in domains:
            domain = domain_info['domain']
            try:
                gtm_setting = GTMSettings.objects.get(domain=domain)
                gtm_settings[domain] = {
                    'container_id': gtm_setting.gtm_container_id,
                    'enabled': gtm_setting.enabled,
                    'created_at': gtm_setting.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'updated_at': gtm_setting.updated_at.strftime('%Y-%m-%d %H:%M:%S')
                }
            except GTMSettings.DoesNotExist:
                gtm_settings[domain] = None
        
        # Statistics
        total_domains = len(domains)
        configured_domains = len([d for d in domains if gtm_settings.get(d['domain'])])
        enabled_domains = len([d for d in domains if gtm_settings.get(d['domain']) and gtm_settings[d['domain']]['enabled']])
        
        context = {
            'plugin_name': 'Google Tag Manager',
            'version': '1.0.0',
            'domains': domains,
            'gtm_settings': gtm_settings,
            'total_domains': total_domains,
            'configured_domains': configured_domains,
            'enabled_domains': enabled_domains,
            'is_admin': currentACL['admin'] == 1
        }
        
        proc = httpProc(request, 'googleTagManager/index.html', context, 'admin')
        return proc.render()
        
    except Exception as e:
        logging.writeToFile(f"Error in GTM main_view: {str(e)}")
        context = {
            'plugin_name': 'Google Tag Manager',
            'version': '1.0.0',
            'error': str(e),
            'domains': [],
            'gtm_settings': {},
            'total_domains': 0,
            'configured_domains': 0,
            'enabled_domains': 0
        }
        proc = httpProc(request, 'googleTagManager/index.html', context, 'admin')
        return proc.render()


@cyberpanel_login_required
def settings_view(request):
    """
    Settings page for configuring GTM container IDs per domain
    """
    mailUtilities.checkHome()
    
    try:
        userID = request.session['userID']
        currentACL = ACLManager.loadedACL(userID)
        
        # Get all user domains
        domains = get_user_domains(userID, currentACL)
        
        # Get existing GTM settings
        gtm_settings = {}
        for domain_info in domains:
            domain = domain_info['domain']
            try:
                gtm_setting = GTMSettings.objects.get(domain=domain)
                gtm_settings[domain] = {
                    'container_id': gtm_setting.gtm_container_id,
                    'enabled': gtm_setting.enabled,
                    'id': gtm_setting.id
                }
            except GTMSettings.DoesNotExist:
                gtm_settings[domain] = None
        
        context = {
            'plugin_name': 'Google Tag Manager',
            'version': '1.0.0',
            'domains': domains,
            'gtm_settings': gtm_settings,
            'is_admin': currentACL['admin'] == 1
        }
        
        proc = httpProc(request, 'googleTagManager/settings.html', context, 'admin')
        return proc.render()
        
    except Exception as e:
        logging.writeToFile(f"Error in GTM settings_view: {str(e)}")
        context = {
            'plugin_name': 'Google Tag Manager',
            'version': '1.0.0',
            'error': str(e),
            'domains': [],
            'gtm_settings': {}
        }
        proc = httpProc(request, 'googleTagManager/settings.html', context, 'admin')
        return proc.render()


@cyberpanel_login_required
@csrf_exempt
@require_http_methods(["GET"])
def api_get_domains(request):
    """
    API endpoint to get list of domains for current user
    """
    try:
        userID = request.session['userID']
        currentACL = ACLManager.loadedACL(userID)
        
        domains = get_user_domains(userID, currentACL)
        
        # Get GTM settings
        domain_list = []
        for domain_info in domains:
            domain = domain_info['domain']
            gtm_setting = get_gtm_for_domain(domain)
            
            domain_list.append({
                'domain': domain,
                'type': domain_info['type'],
                'gtm_configured': gtm_setting is not None,
                'gtm_container_id': gtm_setting.gtm_container_id if gtm_setting else None,
                'gtm_enabled': gtm_setting.enabled if gtm_setting else False
            })
        
        return JsonResponse({
            'success': True,
            'domains': domain_list
        })
        
    except Exception as e:
        logging.writeToFile(f"Error in api_get_domains: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@cyberpanel_login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_save_gtm(request):
    """
    API endpoint to save GTM container ID for a domain
    """
    try:
        userID = request.session['userID']
        currentACL = ACLManager.loadedACL(userID)
        
        data = json.loads(request.body)
        domain = data.get('domain', '').strip()
        container_id = data.get('container_id', '').strip().upper()
        
        if not domain or not container_id:
            return JsonResponse({
                'success': False,
                'error': 'Domain and container ID are required'
            }, status=400)
        
        # Validate domain access
        user_domains = [d['domain'] for d in get_user_domains(userID, currentACL)]
        if domain not in user_domains:
            return JsonResponse({
                'success': False,
                'error': 'You do not have access to this domain'
            }, status=403)
        
        # Validate container ID format
        if not re.match(r'^GTM-[A-Z0-9]+$', container_id):
            # Try to add GTM- prefix if missing
            if not container_id.startswith('GTM-'):
                container_id = f'GTM-{container_id}'
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid GTM container ID format. Must be GTM-XXXXXXX'
                }, status=400)
        
        # Get or create GTM setting
        gtm_setting, created = GTMSettings.objects.get_or_create(
            domain=domain,
            defaults={'gtm_container_id': container_id, 'enabled': True}
        )
        
        if not created:
            # Update existing
            gtm_setting.gtm_container_id = container_id
            gtm_setting.save()
        
        return JsonResponse({
            'success': True,
            'message': 'GTM container ID saved successfully',
            'domain': domain,
            'container_id': container_id,
            'created': created
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logging.writeToFile(f"Error in api_save_gtm: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@cyberpanel_login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_delete_gtm(request):
    """
    API endpoint to delete GTM settings for a domain
    """
    try:
        userID = request.session['userID']
        currentACL = ACLManager.loadedACL(userID)
        
        data = json.loads(request.body)
        domain = data.get('domain', '').strip()
        
        if not domain:
            return JsonResponse({
                'success': False,
                'error': 'Domain is required'
            }, status=400)
        
        # Validate domain access
        user_domains = [d['domain'] for d in get_user_domains(userID, currentACL)]
        if domain not in user_domains:
            return JsonResponse({
                'success': False,
                'error': 'You do not have access to this domain'
            }, status=403)
        
        # Delete GTM setting
        try:
            gtm_setting = GTMSettings.objects.get(domain=domain)
            gtm_setting.delete()
            return JsonResponse({
                'success': True,
                'message': 'GTM settings deleted successfully'
            })
        except GTMSettings.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'GTM settings not found for this domain'
            }, status=404)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logging.writeToFile(f"Error in api_delete_gtm: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@cyberpanel_login_required
@csrf_exempt
@require_http_methods(["GET"])
def api_get_gtm_code(request, domain):
    """
    API endpoint to get GTM code snippets for a domain
    """
    try:
        userID = request.session['userID']
        currentACL = ACLManager.loadedACL(userID)
        
        # Validate domain access
        user_domains = [d['domain'] for d in get_user_domains(userID, currentACL)]
        if domain not in user_domains:
            return JsonResponse({
                'success': False,
                'error': 'You do not have access to this domain'
            }, status=403)
        
        # Get GTM setting
        gtm_setting = get_gtm_for_domain(domain)
        if not gtm_setting:
            return JsonResponse({
                'success': False,
                'error': 'GTM not configured for this domain'
            }, status=404)
        
        # Generate code snippets
        code_snippets = get_gtm_code_full(gtm_setting.gtm_container_id)
        
        return JsonResponse({
            'success': True,
            'domain': domain,
            'container_id': gtm_setting.gtm_container_id,
            'code': code_snippets,
            'instructions': {
                'head': 'Add the code above to your website\'s <head> section, immediately after the opening <head> tag.',
                'body': 'Add the code above to your website\'s <body> section, immediately after the opening <body> tag.'
            }
        })
        
    except Exception as e:
        logging.writeToFile(f"Error in api_get_gtm_code: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@cyberpanel_login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_toggle_gtm(request):
    """
    API endpoint to enable/disable GTM for a domain
    """
    try:
        userID = request.session['userID']
        currentACL = ACLManager.loadedACL(userID)
        
        data = json.loads(request.body)
        domain = data.get('domain', '').strip()
        enabled = data.get('enabled', True)
        
        if not domain:
            return JsonResponse({
                'success': False,
                'error': 'Domain is required'
            }, status=400)
        
        # Validate domain access
        user_domains = [d['domain'] for d in get_user_domains(userID, currentACL)]
        if domain not in user_domains:
            return JsonResponse({
                'success': False,
                'error': 'You do not have access to this domain'
            }, status=403)
        
        # Get GTM setting
        try:
            gtm_setting = GTMSettings.objects.get(domain=domain)
            gtm_setting.enabled = enabled
            gtm_setting.save()
            
            return JsonResponse({
                'success': True,
                'message': f'GTM {"enabled" if enabled else "disabled"} successfully',
                'domain': domain,
                'enabled': enabled
            })
        except GTMSettings.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'GTM settings not found for this domain'
            }, status=404)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logging.writeToFile(f"Error in api_toggle_gtm: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
