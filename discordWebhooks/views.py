# -*- coding: utf-8 -*-
import json
import uuid
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from functools import wraps
from plogical.CyberCPLogFileWriter import CyberCPLogFileWriter as logging
from plogical.acl import ACLManager
from .models import DiscordWebhook, WebhookSettings
from .forms import DiscordWebhookForm, WebhookSettingsForm
from .utils import send_discord_webhook, format_server_usage_embed, get_server_metrics


def _webhooks_json_server_error(exc=None):
    error_id = str(uuid.uuid4())[:12]
    if exc is not None:
        logging.writeToFile('Discord Webhooks error_id=%s: %s' % (error_id, str(exc)))
    else:
        logging.writeToFile('Discord Webhooks error_id=%s' % error_id)
    return JsonResponse(
        {'success': False, 'error': 'Internal server error', 'error_id': error_id},
        status=500,
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


def cyberpanel_admin_required(view_func):
    """Require CyberPanel ACL admin (global webhooks are server-wide sensitive)."""

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        try:
            user_id = request.session['userID']
        except KeyError:
            from loginSystem.views import loadLoginPage

            return redirect(loadLoginPage)
        try:
            acl = ACLManager.loadedACL(user_id)
        except Exception:
            acl = {}
        if acl.get('admin') != 1:
            if view_func.__name__ in ('settings_view', 'discord_webhooks_plugin'):
                return HttpResponse(
                    '<div style="padding:20px;font-family:sans-serif">403 Forbidden: admin access required for Discord Webhooks.</div>',
                    status=403,
                )
            return JsonResponse(
                {'success': False, 'error': 'Admin access required'},
                status=403,
            )
        return view_func(request, *args, **kwargs)

    return _wrapped_view


@cyberpanel_login_required
@cyberpanel_admin_required
def discord_webhooks_plugin(request):
    """Main plugin page (required by CyberPanel)"""
    try:
        # Redirect to settings page as main page
        return redirect('discordWebhooks:settings')
    except Exception as e:
        logging.writeToFile(f"Discord Webhooks plugin error: {str(e)}")
        return HttpResponse('<div>Plugin error</div>', status=500)


@cyberpanel_login_required
@cyberpanel_admin_required
def settings_view(request):
    """Main settings page"""
    try:
        from plogical.mailUtilities import mailUtilities
        from plogical.httpProc import httpProc
        
        mailUtilities.checkHome()
        webhooks = DiscordWebhook.objects.all().order_by('name')
        settings = WebhookSettings.get_settings()
        
        context = {
            'title': 'Discord Webhooks Settings',
            'plugin_name': 'Discord Webhooks',
            'version': '1.0.0',
            'status': 'Active',
            'webhooks': webhooks,
            'settings': settings,
            'webhook_form': DiscordWebhookForm(),
            'settings_form': WebhookSettingsForm(instance=settings)
        }
        
        proc = httpProc(request, 'discordWebhooks/settings.html', context, 'admin')
        return proc.render()
        
    except Exception as e:
        logging.writeToFile(f"Discord Webhooks settings error: {str(e)}")
        return HttpResponse('<div>Settings error</div>', status=500)


@cyberpanel_login_required
@cyberpanel_admin_required
@require_http_methods(["POST"])
def add_webhook(request):
    """Add new webhook"""
    try:
        form = DiscordWebhookForm(request.POST)
        if form.is_valid():
            webhook = form.save()
            messages.success(request, f'Webhook "{webhook.name}" added successfully.')
            logging.writeToFile(f"Discord Webhook added: {webhook.name}")
            return JsonResponse({'success': True, 'message': 'Webhook added successfully'})
        else:
            errors = {field: errors[0] for field, errors in form.errors.items()}
            return JsonResponse({'success': False, 'errors': errors}, status=400)
            
    except Exception as e:
        return _webhooks_json_server_error(e)


@cyberpanel_login_required
@cyberpanel_admin_required
@require_http_methods(["GET", "POST"])
def edit_webhook(request, webhook_id):
    """Edit webhook"""
    try:
        webhook = get_object_or_404(DiscordWebhook, id=webhook_id)
        
        if request.method == 'POST':
            form = DiscordWebhookForm(request.POST, instance=webhook)
            if form.is_valid():
                form.save()
                messages.success(request, f'Webhook "{webhook.name}" updated successfully.')
                logging.writeToFile(f"Discord Webhook updated: {webhook.name}")
                return JsonResponse({'success': True, 'message': 'Webhook updated successfully'})
            else:
                errors = {field: errors[0] for field, errors in form.errors.items()}
                return JsonResponse({'success': False, 'errors': errors}, status=400)
        else:
            # GET request - return webhook data for editing
            return JsonResponse({
                'success': True,
                'webhook': {
                    'id': webhook.id,
                    'name': webhook.name,
                    'url': webhook.url,
                    'enabled': webhook.enabled
                }
            })
            
    except Exception as e:
        return _webhooks_json_server_error(e)


@cyberpanel_login_required
@cyberpanel_admin_required
@require_http_methods(["POST"])
def delete_webhook(request, webhook_id):
    """Delete webhook"""
    try:
        webhook = get_object_or_404(DiscordWebhook, id=webhook_id)
        webhook_name = webhook.name
        webhook.delete()
        messages.success(request, f'Webhook "{webhook_name}" deleted successfully.')
        logging.writeToFile(f"Discord Webhook deleted: {webhook_name}")
        return JsonResponse({'success': True, 'message': 'Webhook deleted successfully'})
        
    except Exception as e:
        return _webhooks_json_server_error(e)


@cyberpanel_login_required
@cyberpanel_admin_required
@require_http_methods(["POST"])
def test_webhook(request, webhook_id):
    """Test webhook"""
    try:
        webhook = get_object_or_404(DiscordWebhook, id=webhook_id)
        
        # Create a test embed
        test_embed = {
            'title': 'Test Webhook',
            'description': 'This is a test message from CyberPanel Discord Webhooks plugin.',
            'color': 3066993,  # Green
            'fields': [
                {
                    'name': 'Webhook Name',
                    'value': webhook.name,
                    'inline': True
                },
                {
                    'name': 'Status',
                    'value': 'Enabled' if webhook.enabled else 'Disabled',
                    'inline': True
                }
            ],
            'footer': {
                'text': 'CyberPanel Discord Webhooks'
            },
            'timestamp': datetime.now().isoformat()
        }
        
        result = send_discord_webhook(webhook.url, {'embeds': [test_embed]})
        
        if result['success']:
            return JsonResponse({
                'success': True,
                'message': f'Test webhook sent successfully to {webhook.name}'
            })
        else:
            logging.writeToFile(
                'Discord Webhooks test_webhook failed for id=%s: %s'
                % (webhook_id, result.get('message', ''))
            )
            return JsonResponse(
                {
                    'success': False,
                    'error': 'Could not send test webhook',
                },
                status=400,
            )
            
    except Exception as e:
        return _webhooks_json_server_error(e)


@cyberpanel_login_required
@cyberpanel_admin_required
@require_http_methods(["POST"])
def save_settings(request):
    """Save plugin settings"""
    try:
        settings = WebhookSettings.get_settings()
        
        # Handle checkbox fields (they don't send value if unchecked)
        post_data = request.POST.copy()
        checkbox_fields = [
            'ssh_logins_enabled', 'security_warnings_enabled', 'server_usage_enabled',
            'server_usage_cpu', 'server_usage_memory', 'server_usage_disk', 'server_usage_network'
        ]
        for field in checkbox_fields:
            if field not in post_data:
                post_data[field] = False
        
        # Handle radio button for threshold_mode (sends "1" or "0" as string)
        if 'server_usage_threshold_mode' in post_data:
            post_data['server_usage_threshold_mode'] = post_data['server_usage_threshold_mode'] == '1'
        else:
            post_data['server_usage_threshold_mode'] = False
        
        form = WebhookSettingsForm(post_data, instance=settings)
        
        if form.is_valid():
            form.save()
            messages.success(request, 'Settings saved successfully.')
            logging.writeToFile("Discord Webhooks settings saved")
            return JsonResponse({'success': True, 'message': 'Settings saved successfully'})
        else:
            errors = {field: errors[0] for field, errors in form.errors.items()}
            return JsonResponse({'success': False, 'errors': errors}, status=400)
            
    except Exception as e:
        return _webhooks_json_server_error(e)
