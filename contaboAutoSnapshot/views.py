# -*- coding: utf-8 -*-
import json
import hashlib
import uuid
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.utils import timezone
from functools import wraps
from plogical.CyberCPLogFileWriter import CyberCPLogFileWriter as logging
from plogical.httpProc import httpProc
from plogical.plugin_acl import require_manage_plugins_api
from .models import ContaboConfig, SnapshotSchedule, SnapshotHistory
from .forms import ContaboConfigForm, ApiCredentialsForm, SnapshotScheduleForm, ManualSnapshotForm
from .utils import get_contabo_api, ContaboAPI
from . import api_encryption

# Plugin configuration
PLUGIN_NAME = 'contaboAutoSnapshot'
PLUGIN_VERSION = '1.0.0'

# Remote verification URLs
REMOTE_VERIFICATION_PATREON_URL = 'https://api.newstargeted.com/api/verify-patreon-membership.php'
REMOTE_VERIFICATION_PAYPAL_URL = 'https://api.newstargeted.com/api/verify-paypal-payment.php'
REMOTE_VERIFICATION_PLUGIN_GRANT_URL = 'https://api.newstargeted.com/api/verify-plugin-grant.php'
REMOTE_ACTIVATION_KEY_URL = 'https://api.newstargeted.com/api/activate-plugin-key.php'
REMOTE_ENTITLEMENT_VERIFY_URL = 'https://api.newstargeted.com/api/verify-entitlement.php'

# Payment URLs (from meta.xml)
PATREON_TIER = 'CyberPanel Paid Plugin'
PATREON_URL = 'https://www.patreon.com/membership/27789984'
PAYPAL_ME_URL = 'https://paypal.me/KimBS?locale.x=en_US&country.x=NO'
PAYPAL_PAYMENT_LINK = ''


def cyberpanel_login_required(view_func):
    """
    Custom decorator that checks for CyberPanel session userID
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        try:
            userID = request.session.get('userID')
            if not userID:
                # Not logged in, redirect to login
                from loginSystem.views import loadLoginPage
                return redirect(loadLoginPage)
            # User is authenticated via CyberPanel session
            return view_func(request, *args, **kwargs)
        except Exception as login_error:
            # Catch any error in login check
            logging.writeToFile(f"Contabo Auto Snapshot: Login check error: {str(login_error)}")
            import traceback
            error_trace = traceback.format_exc()
            logging.writeToFile(f"Contabo Auto Snapshot: Login traceback: {error_trace}")
            # Try to redirect to login, or return error
            try:
                from loginSystem.views import loadLoginPage
                return redirect(loadLoginPage)
            except:
                return HttpResponse(f"<div style='padding: 20px;'><h2>Login Error</h2><p>An error occurred while checking login status.</p><p>Error: {str(login_error)}</p></div>")
    return _wrapped_view


def _api_request(url, data, timeout=10):
    """Send encrypted API request and return decoded response dict."""
    try:
        body, extra_headers = api_encryption.encrypt_payload(data)
        headers = {
            'User-Agent': f'CyberPanel-Plugin/{PLUGIN_VERSION}',
            'X-Plugin-Name': PLUGIN_NAME
        }
        headers.update(extra_headers)
        req = urllib.request.Request(url, data=body, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read()
            ct = response.headers.get('Content-Type', '')
            expect_enc = extra_headers.get('X-Encrypted') == '1'
            return api_encryption.decrypt_response(raw, ct, expect_encrypted=expect_enc)
    except Exception as e:
        logging.writeToFile(f"Contabo Auto Snapshot: API request error to {url}: {str(e)}")
        return {}


def get_server_fingerprint():
    try:
        parts = []
        try:
            with open('/etc/machine-id', 'r') as _mf:
                mid = _mf.read().strip()
                if mid:
                    parts.append(mid)
        except Exception:
            pass
        parts.append(str(uuid.getnode()))
        return hashlib.sha256('|'.join(parts).encode('utf-8')).hexdigest()
    except Exception:
        return ''


def _persist_entitlement_from_response(config, response_data):
    if not config or not response_data:
        return
    try:
        tok = response_data.get('entitlement_token')
        if not tok:
            return
        exp = response_data.get('entitlement_expires_at')
        config.entitlement_token = tok
        fields = ['entitlement_token', 'updated_at']
        if exp is not None:
            try:
                config.entitlement_expires_at = int(exp)
            except (TypeError, ValueError):
                config.entitlement_expires_at = None
            fields.append('entitlement_expires_at')
        config.save(update_fields=fields)
    except Exception as ex:
        logging.writeToFile(f"Contabo Auto Snapshot: Could not persist entitlement: {str(ex)}")


def _clear_entitlement(config):
    if not config:
        return
    try:
        if getattr(config, 'entitlement_token', ''):
            config.entitlement_token = ''
            config.entitlement_expires_at = None
            config.save(update_fields=['entitlement_token', 'entitlement_expires_at', 'updated_at'])
    except Exception as ex:
        logging.writeToFile(f"Contabo Auto Snapshot: Could not clear entitlement: {str(ex)}")


def check_plugin_grant(user_email, user_ip='', domain='', server_fp=''):
    """Check Plugin Grants from api.newstargeted.com (manual grants from admin panel)"""
    try:
        # Normalize email to lowercase for matching
        user_email_normalized = (user_email or '').strip().lower()
        request_data = {
            'user_email': user_email_normalized,
            'plugin_name': PLUGIN_NAME,
            'user_ip': user_ip,
            'domain': domain,
            'server_fingerprint': server_fp,
        }
        data = _api_request(REMOTE_VERIFICATION_PLUGIN_GRANT_URL, request_data)
        if data.get('success') and data.get('has_access'):
            logging.writeToFile(f"Contabo Auto Snapshot: Plugin grant access granted for {user_email_normalized}")
            _persist_entitlement_from_response(ContaboConfig.get_config(), data)
            return {'has_access': True, 'message': data.get('message', 'Access granted via Plugin Grants')}
        logging.writeToFile(f"Contabo Auto Snapshot: Plugin grant check - no access for {user_email_normalized}: {data.get('message', 'No grant found')}")
        return {'has_access': False, 'message': data.get('message', '')}
    except Exception as e:
        logging.writeToFile(f"Contabo Auto Snapshot: Plugin grant check error: {str(e)}")
        return {'has_access': False, 'message': ''}


def check_patreon_membership(user_email, user_ip='', domain='', server_fp=''):
    """Check Patreon membership via remote verification server"""
    try:
        request_data = {
            'user_email': user_email,
            'plugin_name': PLUGIN_NAME,
            'plugin_version': PLUGIN_VERSION,
            'user_ip': user_ip,
            'domain': domain,
            'server_fingerprint': server_fp,
            'tier_id': '27789984'  # CyberPanel Paid Plugin tier ID
        }
        response_data = _api_request(REMOTE_VERIFICATION_PATREON_URL, request_data)
        if response_data.get('success', False):
            if response_data.get('has_access'):
                _persist_entitlement_from_response(ContaboConfig.get_config(), response_data)
            return {
                'has_access': response_data.get('has_access', False),
                'patreon_tier': response_data.get('patreon_tier', PATREON_TIER),
                'patreon_url': response_data.get('patreon_url', PATREON_URL),
                'message': response_data.get('message', 'Access granted'),
                'error': None
            }
        return {
            'has_access': False,
            'patreon_tier': PATREON_TIER,
            'patreon_url': PATREON_URL,
            'message': response_data.get('message', 'Patreon subscription required'),
            'error': response_data.get('error')
        }
    except urllib.error.URLError as e:
        logging.writeToFile(f"Error checking Patreon membership: {str(e)}")
        return {
            'has_access': False,
            'patreon_tier': PATREON_TIER,
            'patreon_url': PATREON_URL,
            'message': 'Unable to verify Patreon membership. Please try again later.',
            'error': str(e)
        }
    except Exception as e:
        logging.writeToFile(f"Error checking Patreon membership: {str(e)}")
        return {
            'has_access': False,
            'patreon_tier': PATREON_TIER,
            'patreon_url': PATREON_URL,
            'message': 'Error verifying Patreon membership',
            'error': str(e)
        }


def check_paypal_payment(user_email, user_ip='', domain='', server_fp=''):
    """Check PayPal payment via remote verification server"""
    try:
        request_data = {
            'user_email': user_email,
            'plugin_name': PLUGIN_NAME,
            'plugin_version': PLUGIN_VERSION,
            'user_ip': user_ip,
            'domain': domain,
            'server_fingerprint': server_fp,
            'timestamp': int(datetime.now().timestamp())
        }
        response_data = _api_request(REMOTE_VERIFICATION_PAYPAL_URL, request_data)
        if response_data.get('success', False):
            if response_data.get('has_access'):
                _persist_entitlement_from_response(ContaboConfig.get_config(), response_data)
            return {
                'has_access': response_data.get('has_access', False),
                'paypal_me_url': response_data.get('paypal_me_url', PAYPAL_ME_URL),
                'paypal_payment_link': response_data.get('paypal_payment_link', PAYPAL_PAYMENT_LINK),
                'message': response_data.get('message', 'Access granted'),
                'error': None
            }
        return {
            'has_access': False,
            'paypal_me_url': PAYPAL_ME_URL,
            'paypal_payment_link': PAYPAL_PAYMENT_LINK,
            'message': response_data.get('message', 'PayPal payment required'),
            'error': response_data.get('error')
        }
    except urllib.error.URLError as e:
        logging.writeToFile(f"Error checking PayPal payment: {str(e)}")
        return {
            'has_access': False,
            'paypal_me_url': PAYPAL_ME_URL,
            'paypal_payment_link': PAYPAL_PAYMENT_LINK,
            'message': 'Unable to verify PayPal payment. Please try again later.',
            'error': str(e)
        }
    except Exception as e:
        logging.writeToFile(f"Error checking PayPal payment: {str(e)}")
        return {
            'has_access': False,
            'paypal_me_url': PAYPAL_ME_URL,
            'paypal_payment_link': PAYPAL_PAYMENT_LINK,
            'message': 'Error verifying PayPal payment',
            'error': str(e)
        }


def unified_verification_required(view_func):
    """
    Unified decorator that checks payment based on user's preferred method
    Supports both Patreon and PayPal, and allows user to choose
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        try:
            # First check login
            try:
                userID = request.session['userID']
            except KeyError:
                from loginSystem.views import loadLoginPage
                return redirect(loadLoginPage)
            
            # Get user email and normalize to lowercase for matching
            user_email = getattr(request.user, 'email', None) if hasattr(request, 'user') and request.user else None
            if not user_email:
                user_email = request.session.get('email', '') or getattr(request.user, 'username', '')
            user_email = user_email.strip().lower() if user_email else ''
            logging.writeToFile(f"Contabo Auto Snapshot: Checking access for email: {user_email}")
            
            # Get payment method preference from config (with error handling)
            try:
                config = ContaboConfig.get_config()
                payment_method = config.payment_method if hasattr(config, 'payment_method') else 'both'
            except Exception as config_error:
                # If config can't be loaded, default to 'both' and log the error
                logging.writeToFile(f"Contabo Auto Snapshot: Could not load config in decorator: {str(config_error)}")
                payment_method = 'both'
            
            has_access = False
            verification_result = {}

            user_ip = request.META.get('REMOTE_ADDR', '') or ''
            domain = request.get_host() or ''
            server_fp = get_server_fingerprint()

            try:
                cfg_ent = ContaboConfig.get_config()
                ent_tok = (getattr(cfg_ent, 'entitlement_token', '') or '').strip()
                if ent_tok:
                    ent_resp = _api_request(REMOTE_ENTITLEMENT_VERIFY_URL, {
                        'entitlement_token': ent_tok,
                        'plugin_name': PLUGIN_NAME,
                        'user_email': user_email,
                        'server_fingerprint': server_fp,
                        'domain': domain,
                    })
                    if ent_resp.get('success') and ent_resp.get('has_access'):
                        _persist_entitlement_from_response(cfg_ent, ent_resp)
                        request.session['contabo_premium_access_via'] = 'entitlement'
                        return view_func(request, *args, **kwargs)
                    _clear_entitlement(ContaboConfig.get_config())
            except Exception as _ent_e:
                logging.writeToFile(f"Contabo Auto Snapshot: Entitlement verify error: {str(_ent_e)}")
            
            # First check for activation key (from request or stored in config)
            activation_key = request.GET.get('activation_key') or request.POST.get('activation_key')
            if (
                not activation_key
                and request.method == 'POST'
                and request.content_type
                and 'application/json' in request.content_type
                and request.body
            ):
                try:
                    _payload = json.loads(request.body)
                    if isinstance(_payload, dict):
                        activation_key = _payload.get('activation_key') or activation_key
                except (json.JSONDecodeError, ValueError, TypeError):
                    pass
            if not activation_key:
                try:
                    config = ContaboConfig.get_config()
                    activation_key = getattr(config, 'activation_key', '') or ''
                except Exception:
                    activation_key = ''
            if activation_key:
                try:
                    request_data = {
                        'activation_key': activation_key.strip(),
                        'plugin_name': PLUGIN_NAME,
                        'user_email': user_email,
                        'server_fingerprint': server_fp,
                        'domain': domain,
                    }
                    response_data = _api_request(REMOTE_ACTIVATION_KEY_URL, request_data)
                    if response_data.get('success', False) and response_data.get('has_access', False):
                        has_access = True
                        verification_result = {
                            'method': 'activation_key',
                            'has_access': True,
                            'message': response_data.get('message', 'Access activated via key'),
                            'grant_type': response_data.get('grant_type', 'manual')
                        }
                        try:
                            config = ContaboConfig.get_config()
                            config.activation_key = activation_key.strip()
                            config.save(update_fields=['activation_key', 'updated_at'])
                            _persist_entitlement_from_response(config, response_data)
                        except Exception as persist_err:
                            logging.writeToFile(f"Contabo Auto Snapshot: Could not persist activation key: {str(persist_err)}")
                    elif not response_data.get('success') and activation_key:
                        try:
                            config = ContaboConfig.get_config()
                            if getattr(config, 'activation_key', '') == activation_key.strip():
                                config.activation_key = ''
                                config.save(update_fields=['activation_key', 'updated_at'])
                        except Exception:
                            pass
                except Exception as key_error:
                    logging.writeToFile(f"Contabo Auto Snapshot: Activation key check error: {str(key_error)}")
            
            # If activation key didn't grant access, check Plugin Grants (api.newstargeted.com admin)
            if not has_access:
                grant_result = check_plugin_grant(
                    user_email,
                    user_ip,
                    domain,
                    server_fp,
                )
                if grant_result.get('has_access'):
                    has_access = True
                    verification_result = {
                        'method': 'plugin_grant',
                        'has_access': True,
                        'message': grant_result.get('message', 'Access granted via Plugin Grants')
                    }
            
            # If still no access, check Patreon/PayPal
            if not has_access:
                try:
                    if payment_method == 'patreon':
                        result = check_patreon_membership(
                            user_email,
                            user_ip,
                            domain,
                            server_fp,
                        )
                        has_access = result.get('has_access', False)
                        verification_result = {
                            'method': 'patreon',
                            'has_access': has_access,
                            'patreon_tier': result.get('patreon_tier', PATREON_TIER),
                            'patreon_url': result.get('patreon_url', PATREON_URL),
                            'message': result.get('message', 'Patreon subscription required'),
                            'error': result.get('error')
                        }
                    elif payment_method == 'paypal':
                        result = check_paypal_payment(
                            user_email,
                            user_ip,
                            domain,
                            server_fp,
                        )
                        has_access = result.get('has_access', False)
                        verification_result = {
                            'method': 'paypal',
                            'has_access': has_access,
                            'paypal_me_url': result.get('paypal_me_url', PAYPAL_ME_URL),
                            'paypal_payment_link': result.get('paypal_payment_link', PAYPAL_PAYMENT_LINK),
                            'message': result.get('message', 'PayPal payment required'),
                            'error': result.get('error')
                        }
                    else:  # 'both' - check both methods
                        patreon_result = check_patreon_membership(
                            user_email,
                            user_ip,
                            domain,
                            server_fp,
                        )
                        paypal_result = check_paypal_payment(
                            user_email,
                            user_ip,
                            domain,
                            server_fp,
                        )
                        
                        has_access = patreon_result.get('has_access', False) or paypal_result.get('has_access', False)
                        verification_result = {
                            'method': 'both',
                            'has_access': has_access,
                            'patreon_result': patreon_result,
                            'paypal_result': paypal_result,
                            'patreon_tier': patreon_result.get('patreon_tier', PATREON_TIER),
                            'patreon_url': patreon_result.get('patreon_url', PATREON_URL),
                            'paypal_me_url': paypal_result.get('paypal_me_url', PAYPAL_ME_URL),
                            'paypal_payment_link': paypal_result.get('paypal_payment_link', PAYPAL_PAYMENT_LINK),
                            'message': 'Payment or subscription required' if not has_access else 'Access granted'
                        }
                except Exception as verify_error:
                    # If verification fails, log error but don't crash - show subscription required page
                    logging.writeToFile(f"Contabo Auto Snapshot: Verification error in decorator: {str(verify_error)}")
                    import traceback
                    error_trace = traceback.format_exc()
                    logging.writeToFile(f"Contabo Auto Snapshot: Verification traceback: {error_trace}")
                    has_access = False
                    verification_result = {
                        'method': payment_method,
                        'has_access': False,
                        'patreon_tier': PATREON_TIER,
                        'patreon_url': PATREON_URL,
                        'paypal_me_url': PAYPAL_ME_URL,
                        'paypal_payment_link': PAYPAL_PAYMENT_LINK,
                        'message': 'Unable to verify access. Please try again later.',
                        'error': str(verify_error)
                    }
            
            if not has_access:
                # User doesn't have access - show subscription required page
                try:
                    from plogical.httpProc import httpProc
                    context = {
                        'plugin_name': 'Auto Snapshot for Contabo',
                        'is_paid': True,
                        'payment_method': payment_method,
                        'verification_result': verification_result,
                        'patreon_tier': verification_result.get('patreon_tier', PATREON_TIER),
                        'patreon_url': verification_result.get('patreon_url', PATREON_URL),
                        'paypal_me_url': verification_result.get('paypal_me_url', PAYPAL_ME_URL),
                        'paypal_payment_link': verification_result.get('paypal_payment_link', PAYPAL_PAYMENT_LINK),
                        'message': verification_result.get('message', 'Payment or subscription required'),
                        'error': verification_result.get('error')
                    }
                    proc = httpProc(request, 'contaboAutoSnapshot/subscription_required.html', context, 'managePlugins')
                    return proc.render()
                except Exception as render_error:
                    # If rendering fails, return a simple error page
                    logging.writeToFile(f"Contabo Auto Snapshot: Error rendering subscription required page: {str(render_error)}")
                    import traceback
                    error_trace = traceback.format_exc()
                    logging.writeToFile(f"Contabo Auto Snapshot: Render traceback: {error_trace}")
                    return HttpResponse(f"<div style='padding: 20px;'><h2>Subscription Required</h2><p>This plugin requires a premium subscription. Please subscribe to access this plugin.</p><p>Error: {str(render_error)}</p><pre>{error_trace}</pre></div>")
            
            # User has access - store how they got it (template hides payment UI when whitelisted)
            if has_access and verification_result:
                request.session['contabo_premium_access_via'] = verification_result.get('method', '')
            # User has access - proceed with view
            try:
                return view_func(request, *args, **kwargs)
            except Exception as view_error:
                # If the view itself fails, log and return error
                logging.writeToFile(f"Contabo Auto Snapshot: Error in view function: {str(view_error)}")
                import traceback
                error_trace = traceback.format_exc()
                logging.writeToFile(f"Contabo Auto Snapshot: View traceback: {error_trace}")
                return HttpResponse(f"<div style='padding: 20px;'><h2>Plugin Error</h2><p>An error occurred while loading the plugin settings.</p><p>Error: {str(view_error)}</p><pre>{error_trace}</pre></div>")
        except Exception as decorator_error:
            # Catch any error in the decorator itself
            logging.writeToFile(f"Contabo Auto Snapshot: Error in decorator: {str(decorator_error)}")
            import traceback
            error_trace = traceback.format_exc()
            logging.writeToFile(f"Contabo Auto Snapshot: Decorator traceback: {error_trace}")
            # Return a simple error page - don't try to render template if decorator failed
            return HttpResponse(f"<div style='padding: 20px;'><h2>Plugin Error</h2><p>An error occurred in the verification system.</p><p>Error: {str(decorator_error)}</p><pre>{error_trace}</pre></div>")
    
    return _wrapped_view


def test_view_no_decorator(request):
    """Test view with NO decorators at all"""
    return HttpResponse("<h1>Test View Works!</h1><p>If you see this, the basic view system is working.</p><p>No decorators used.</p>")


@cyberpanel_login_required
def main_view(request):
    """Main plugin page (required by CyberPanel)"""
    try:
        # Redirect to settings page as main page
        return redirect('contaboAutoSnapshot:settings')
    except Exception as e:
        logging.writeToFile(f"Contabo Auto Snapshot plugin error: {str(e)}")
        return HttpResponse(f"<div>Plugin Error: {str(e)}</div>")


@cyberpanel_login_required
@unified_verification_required
def settings_view(request):
    """Main settings page"""
    try:
        from plogical.mailUtilities import mailUtilities
        from plogical.httpProc import httpProc
        
        mailUtilities.checkHome()
        
        try:
            config = ContaboConfig.get_config()
        except Exception as db_error:
            logging.writeToFile(f"Contabo Auto Snapshot database error: {str(db_error)}")
            import traceback
            error_trace = traceback.format_exc()
            logging.writeToFile(f"Contabo Auto Snapshot database traceback: {error_trace}")
            # Create a default config object if database is not ready
            from django.db import connection
            try:
                # Try to create tables if they don't exist
                from django.core.management import call_command
                call_command('migrate', 'contaboAutoSnapshot', verbosity=0, interactive=False)
                config = ContaboConfig.get_config()
            except Exception as migrate_error:
                logging.writeToFile(f"Contabo Auto Snapshot migration error: {str(migrate_error)}")
                migrate_trace = traceback.format_exc()
                logging.writeToFile(f"Contabo Auto Snapshot migration traceback: {migrate_trace}")
                # Return error page if database is not ready
                return HttpResponse(f"<div style='padding: 20px;'><h2>Database Error</h2><p>The plugin database tables need to be created. Please run migrations or reinstall the plugin.</p><p>Error: {str(db_error)}</p><pre>{error_trace}</pre></div>")
        
        try:
            schedules = SnapshotSchedule.objects.all().order_by('name')
        except Exception as schedule_error:
            logging.writeToFile(f"Contabo Auto Snapshot: Error loading schedules: {str(schedule_error)}")
            schedules = []
        
        try:
            recent_snapshots = SnapshotHistory.objects.all().order_by('-created_at')[:10]
        except Exception as snapshot_error:
            logging.writeToFile(f"Contabo Auto Snapshot: Error loading snapshots: {str(snapshot_error)}")
            recent_snapshots = []
        
        # Hide activation/payment UI when whitelisted (Plugin Grants or activation key)
        access_via = request.session.get('contabo_premium_access_via', '')
        show_payment_ui = access_via not in ('plugin_grant', 'activation_key', 'entitlement')
        
        context = {
            'title': 'Auto Snapshot for Contabo',
            'plugin_name': 'Auto Snapshot for Contabo',
            'version': '1.0.0',
            'status': 'Active',
            'config': config,
            'config_form': ContaboConfigForm(instance=config),
            'schedules': schedules,
            'recent_snapshots': recent_snapshots,
            'schedule_form': SnapshotScheduleForm(),
            'manual_snapshot_form': ManualSnapshotForm(),
            'show_payment_ui': show_payment_ui,
            'access_via_grant_or_key': not show_payment_ui,
        }
        
        try:
            proc = httpProc(request, 'contaboAutoSnapshot/settings.html', context, 'managePlugins')
            return proc.render()
        except Exception as render_error:
            logging.writeToFile(f"Contabo Auto Snapshot: Template render error: {str(render_error)}")
            import traceback
            render_trace = traceback.format_exc()
            logging.writeToFile(f"Contabo Auto Snapshot: Render traceback: {render_trace}")
            # Return a simple HTML page instead
            return HttpResponse(f"<div style='padding: 20px;'><h2>Auto Snapshot for Contabo</h2><p>Settings page is loading...</p><p>If you see this message, there may be a template issue.</p><p>Error: {str(render_error)}</p></div>")
        
    except Exception as e:
        logging.writeToFile(f"Contabo Auto Snapshot settings error: {str(e)}")
        import traceback
        error_trace = traceback.format_exc()
        logging.writeToFile(f"Contabo Auto Snapshot traceback: {error_trace}")
        return HttpResponse(f"<div style='padding: 20px;'><h2>Settings Error</h2><p>{str(e)}</p><pre>{error_trace}</pre></div>")


@cyberpanel_login_required
@require_http_methods(["POST"])
def activate_key(request):
    """Activate plugin access using activation key"""
    try:
        import json
        from django.http import JsonResponse
        
        # Get activation key from POST data
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST
        
        activation_key = data.get('activation_key', '').strip()
        user_email = data.get('user_email', '').strip()
        
        if not activation_key:
            return JsonResponse({
                'success': False,
                'message': 'Activation key is required'
            }, status=400)
        
        # Get user email from session if not provided
        if not user_email:
            user_email = request.session.get('email', '') or getattr(request.user, 'email', '') if hasattr(request, 'user') and request.user else ''
        
        request_data = {
            'activation_key': activation_key,
            'plugin_name': PLUGIN_NAME,
            'user_email': user_email,
            'server_fingerprint': get_server_fingerprint(),
            'domain': request.get_host() or '',
        }
        response_data = _api_request(REMOTE_ACTIVATION_KEY_URL, request_data)
        if response_data.get('success', False) and response_data.get('has_access', False):
            try:
                config = ContaboConfig.get_config()
                config.activation_key = activation_key
                config.save(update_fields=['activation_key', 'updated_at'])
                _persist_entitlement_from_response(config, response_data)
            except Exception as persist_err:
                logging.writeToFile(f"Contabo Auto Snapshot: Could not persist activation key: {str(persist_err)}")
            return JsonResponse({
                'success': True,
                'has_access': True,
                'message': response_data.get('message', 'Access activated successfully'),
                'grant_type': response_data.get('grant_type', 'manual'),
                'expires_at': response_data.get('expires_at')
            })
        return JsonResponse({
            'success': False,
            'has_access': False,
            'message': response_data.get('message', 'Invalid activation key'),
            'error': response_data.get('error')
        }, status=400)
                
    except urllib.error.URLError as e:
        logging.writeToFile(f"Error activating key: {str(e)}")
        return JsonResponse({
            'success': False,
            'has_access': False,
            'message': 'Unable to activate. Please try again later.',
            'error': str(e)
        }, status=500)
    except Exception as e:
        logging.writeToFile(f"Error activating key: {str(e)}")
        import traceback
        error_trace = traceback.format_exc()
        logging.writeToFile(f"Activation traceback: {error_trace}")
        return JsonResponse({
            'success': False,
            'has_access': False,
            'message': 'Error activating access',
            'error': str(e)
        }, status=500)


@cyberpanel_login_required
@require_manage_plugins_api
@unified_verification_required
@require_http_methods(["POST"])
def add_schedule(request):
    """Add new snapshot schedule"""
    try:
        # Check if auto backup is enabled globally (warning only, don't block)
        config = ContaboConfig.get_config()
        if not config.auto_backup_enabled:
            # Allow creation but warn user
            pass
        
        form = SnapshotScheduleForm(request.POST)
        if form.is_valid():
            schedule = form.save()
            messages.success(request, f'Schedule "{schedule.name}" added successfully.')
            logging.writeToFile(f"Snapshot schedule added: {schedule.name}")
            return JsonResponse({'success': True, 'message': 'Schedule added successfully'})
        else:
            errors = {field: errors[0] for field, errors in form.errors.items()}
            return JsonResponse({'success': False, 'errors': errors}, status=400)
            
    except Exception as e:
        logging.writeToFile(f"Error adding schedule: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@cyberpanel_login_required
@require_manage_plugins_api
@unified_verification_required
@require_http_methods(["GET", "POST"])
def edit_schedule(request, schedule_id):
    """Edit snapshot schedule"""
    try:
        schedule = get_object_or_404(SnapshotSchedule, id=schedule_id)
        
        if request.method == 'POST':
            form = SnapshotScheduleForm(request.POST, instance=schedule)
            if form.is_valid():
                form.save()
                messages.success(request, f'Schedule "{schedule.name}" updated successfully.')
                logging.writeToFile(f"Snapshot schedule updated: {schedule.name}")
                return JsonResponse({'success': True, 'message': 'Schedule updated successfully'})
            else:
                errors = {field: errors[0] for field, errors in form.errors.items()}
                return JsonResponse({'success': False, 'errors': errors}, status=400)
        else:
            # GET request - return schedule data for editing
            return JsonResponse({
                'success': True,
                'schedule': {
                    'id': schedule.id,
                    'name': schedule.name,
                    'vps_id': schedule.vps_id,
                    'schedule_type': schedule.schedule_type,
                    'cron_expression': schedule.cron_expression,
                    'snapshot_name_prefix': schedule.snapshot_name_prefix,
                    'include_ram': schedule.include_ram,
                    'description_template': schedule.description_template,
                    'retention_count': schedule.retention_count,
                    'auto_delete_old': schedule.auto_delete_old,
                    'enabled': schedule.enabled,
                }
            })
            
    except Exception as e:
        logging.writeToFile(f"Error editing schedule: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@cyberpanel_login_required
@require_manage_plugins_api
@require_http_methods(["POST"])
def delete_schedule(request, schedule_id):
    """Delete snapshot schedule"""
    try:
        schedule = get_object_or_404(SnapshotSchedule, id=schedule_id)
        schedule_name = schedule.name
        schedule.delete()
        messages.success(request, f'Schedule "{schedule_name}" deleted successfully.')
        logging.writeToFile(f"Snapshot schedule deleted: {schedule_name}")
        return JsonResponse({'success': True, 'message': 'Schedule deleted successfully'})
        
    except Exception as e:
        logging.writeToFile(f"Error deleting schedule: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@cyberpanel_login_required
@require_manage_plugins_api
@require_http_methods(["POST"])
def toggle_schedule(request, schedule_id):
    """Toggle schedule enabled/disabled"""
    try:
        schedule = get_object_or_404(SnapshotSchedule, id=schedule_id)
        schedule.enabled = not schedule.enabled
        schedule.save()
        
        status = 'enabled' if schedule.enabled else 'disabled'
        messages.success(request, f'Schedule "{schedule.name}" {status}.')
        logging.writeToFile(f"Snapshot schedule {status}: {schedule.name}")
        return JsonResponse({
            'success': True,
            'message': f'Schedule {status} successfully',
            'enabled': schedule.enabled
        })
        
    except Exception as e:
        logging.writeToFile(f"Error toggling schedule: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@cyberpanel_login_required
@require_manage_plugins_api
@unified_verification_required
@require_http_methods(["POST"])
def create_snapshot(request):
    """Manually create a snapshot"""
    try:
        form = ManualSnapshotForm(request.POST)
        if form.is_valid():
            vps_id = form.cleaned_data['vps_id']
            snapshot_name = form.cleaned_data['snapshot_name']
            description = form.cleaned_data.get('description', '')
            include_ram = form.cleaned_data.get('include_ram', False)
            
            # Create snapshot history record
            snapshot_history = SnapshotHistory.objects.create(
                vps_id=vps_id,
                snapshot_name=snapshot_name,
                description=description,
                status='creating'
            )
            
            # Get API client and create snapshot
            api = get_contabo_api()
            result = api.create_snapshot(vps_id, snapshot_name, description, include_ram)
            
            if result['success']:
                snapshot_history.status = 'completed'
                snapshot_history.completed_at = timezone.now()
                if 'data' in result and 'id' in result['data']:
                    snapshot_history.snapshot_id = str(result['data']['id'])
                snapshot_history.save()
                
                messages.success(request, f'Snapshot "{snapshot_name}" created successfully.')
                logging.writeToFile(f"Manual snapshot created: {snapshot_name}")
                return JsonResponse({
                    'success': True,
                    'message': f'Snapshot "{snapshot_name}" created successfully'
                })
            else:
                snapshot_history.status = 'failed'
                snapshot_history.error_message = result.get('message', 'Unknown error')
                snapshot_history.completed_at = timezone.now()
                snapshot_history.save()
                
                return JsonResponse({
                    'success': False,
                    'error': result.get('message', 'Failed to create snapshot')
                }, status=400)
        else:
            errors = {field: errors[0] for field, errors in form.errors.items()}
            return JsonResponse({'success': False, 'errors': errors}, status=400)
            
    except Exception as e:
        logging.writeToFile(f"Error creating snapshot: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@cyberpanel_login_required
def snapshot_history(request):
    """View snapshot history"""
    try:
        from plogical.mailUtilities import mailUtilities
        from plogical.httpProc import httpProc
        
        mailUtilities.checkHome()
        
        snapshots = SnapshotHistory.objects.all().order_by('-created_at')
        
        context = {
            'title': 'Snapshot History',
            'plugin_name': 'Auto Snapshot for Contabo',
            'snapshots': snapshots,
        }
        
        proc = httpProc(request, 'contaboAutoSnapshot/history.html', context, 'managePlugins')
        return proc.render()
        
    except Exception as e:
        logging.writeToFile(f"Error viewing snapshot history: {str(e)}")
        return HttpResponse(f"<div>History Error: {str(e)}</div>")


@cyberpanel_login_required
@require_manage_plugins_api
@require_http_methods(["POST"])
def delete_snapshot(request, snapshot_id):
    """Delete snapshot from history (and optionally from Contabo)"""
    try:
        snapshot = get_object_or_404(SnapshotHistory, id=snapshot_id)
        snapshot_name = snapshot.snapshot_name
        
        # Optionally delete from Contabo API if snapshot_id is available
        if snapshot.snapshot_id and request.POST.get('delete_from_contabo') == 'true':
            try:
                api = get_contabo_api()
                result = api.delete_snapshot(snapshot.vps_id, snapshot.snapshot_id)
                if not result['success']:
                    logging.writeToFile(f"Warning: Failed to delete snapshot from Contabo: {result.get('message')}")
            except Exception as e:
                logging.writeToFile(f"Warning: Error deleting snapshot from Contabo: {str(e)}")
        
        snapshot.delete()
        messages.success(request, f'Snapshot "{snapshot_name}" deleted from history.')
        logging.writeToFile(f"Snapshot deleted from history: {snapshot_name}")
        return JsonResponse({'success': True, 'message': 'Snapshot deleted successfully'})
        
    except Exception as e:
        logging.writeToFile(f"Error deleting snapshot: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@cyberpanel_login_required
@require_manage_plugins_api
@require_http_methods(["GET"])
def api_schedules(request):
    """API endpoint to get all schedules"""
    try:
        schedules = SnapshotSchedule.objects.all().order_by('name')
        data = [{
            'id': s.id,
            'name': s.name,
            'vps_id': s.vps_id,
            'schedule_type': s.schedule_type,
            'enabled': s.enabled,
            'last_run': s.last_run.isoformat() if s.last_run else None,
            'next_run': s.next_run.isoformat() if s.next_run else None,
        } for s in schedules]
        
        return JsonResponse({'success': True, 'data': data})
        
    except Exception as e:
        logging.writeToFile(f"Error in api_schedules: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@cyberpanel_login_required
@require_manage_plugins_api
@require_http_methods(["GET"])
def api_snapshots(request):
    """API endpoint to get snapshot history"""
    try:
        limit = int(request.GET.get('limit', 50))
        snapshots = SnapshotHistory.objects.all().order_by('-created_at')[:limit]
        data = [{
            'id': s.id,
            'vps_id': s.vps_id,
            'snapshot_name': s.snapshot_name,
            'snapshot_id': s.snapshot_id,
            'description': s.description,
            'status': s.status,
            'error_message': s.error_message,
            'created_at': s.created_at.isoformat(),
            'completed_at': s.completed_at.isoformat() if s.completed_at else None,
        } for s in snapshots]
        
        return JsonResponse({'success': True, 'data': data})
        
    except Exception as e:
        logging.writeToFile(f"Error in api_snapshots: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@cyberpanel_login_required
@require_manage_plugins_api
@require_http_methods(["POST"])
def test_connection(request):
    """Test Contabo API connection and save config"""
    try:
        config = ContaboConfig.get_config()
        form = ApiCredentialsForm(request.POST, instance=config)
        if form.is_valid():
            form.save()
            logging.writeToFile("Contabo Auto Snapshot API config saved")
        else:
            errors = {field: errors[0] for field, errors in form.errors.items()}
            return JsonResponse({'success': False, 'errors': errors}, status=400)
        
        # Test connection if API credentials are provided
        if config.api_client_id and config.api_client_secret and config.api_key and config.api_secret:
            try:
                api = get_contabo_api()
                result = api.test_connection()
                if result.get('success') and 'plan_max_snapshots' in result:
                    config.api_tested = True
                    config.api_max_snapshots_from_plan = result['plan_max_snapshots']
                    # Cap max_snapshots_per_vps to plan limit
                    if config.max_snapshots_per_vps > (config.api_max_snapshots_from_plan or 1):
                        config.max_snapshots_per_vps = config.api_max_snapshots_from_plan or 1
                    config.save(update_fields=['api_tested', 'api_max_snapshots_from_plan', 'max_snapshots_per_vps', 'updated_at'])
                return JsonResponse(result)
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': f'Error testing connection: {str(e)}'
                }, status=500)
        else:
            return JsonResponse({
                'success': True,
                'message': 'Configuration saved successfully. Please enter API credentials to test connection.'
            })
        
    except Exception as e:
        logging.writeToFile(f"Error testing connection: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=500)


@cyberpanel_login_required
@require_manage_plugins_api
@require_http_methods(["POST"])
def save_config(request):
    """Save Contabo configuration (API credentials, max snapshots, auto backup). Runs API test when credentials present."""
    try:
        config = ContaboConfig.get_config()
        form = ContaboConfigForm(request.POST, instance=config)
        
        if form.is_valid():
            form.save()
            messages.success(request, 'Configuration saved successfully.')
            logging.writeToFile("Contabo Auto Snapshot config saved")
            msg = 'Configuration saved.'
            # Test connection if API credentials are present
            if config.api_client_id and config.api_client_secret and config.api_key and config.api_secret:
                try:
                    api = get_contabo_api()
                    result = api.test_connection()
                    if result.get('success'):
                        config.api_tested = True
                        config.api_max_snapshots_from_plan = result.get('plan_max_snapshots')
                        if config.max_snapshots_per_vps > (config.api_max_snapshots_from_plan or 1):
                            config.max_snapshots_per_vps = config.api_max_snapshots_from_plan or 1
                        config.save(update_fields=['api_tested', 'api_max_snapshots_from_plan', 'max_snapshots_per_vps', 'updated_at'])
                        msg = result.get('message', msg)
                    else:
                        msg = result.get('message', msg)
                except Exception as te:
                    logging.writeToFile(f"Contabo API test after save: {str(te)}")
                    msg = f'Saved. API test failed: {str(te)}'
            return JsonResponse({'success': True, 'message': msg})
        else:
            errors = {field: errors[0] for field, errors in form.errors.items()}
            return JsonResponse({'success': False, 'errors': errors}, status=400)
            
    except Exception as e:
        logging.writeToFile(f"Error saving config: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
