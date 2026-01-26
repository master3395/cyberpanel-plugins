# -*- coding: utf-8 -*-
"""
Discord Authentication Views
Handles Discord OAuth2 login flow and account management
"""

from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from functools import wraps
import json
from loginSystem.models import Administrator
from plogical.httpProc import httpProc
from plogical.mailUtilities import mailUtilities
from plogical.CyberCPLogFileWriter import CyberCPLogFileWriter as logging
from plogical.acl import ACLManager
from .models import DiscordAccount, DiscordAuthSettings
from .utils.discord_oauth import (
    get_authorization_url,
    exchange_code_for_token,
    get_discord_user,
    generate_state
)
from .utils.config import get_config, save_config, is_enabled


def cyberpanel_login_required(view_func):
    """Decorator to check CyberPanel session"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        try:
            userID = request.session['userID']
            return view_func(request, *args, **kwargs)
        except KeyError:
            from loginSystem.views import loadLoginPage
            return redirect(loadLoginPage)
    return _wrapped_view


@csrf_exempt
@require_http_methods(["GET"])
def check_enabled(request):
    """Check if Discord authentication is enabled (for JS injection)"""
    try:
        enabled = is_enabled()
        return JsonResponse({'enabled': enabled})
    except Exception as e:
        return JsonResponse({'enabled': False})


@csrf_exempt
@require_http_methods(["GET"])
def discord_login(request):
    """
    Initiate Discord OAuth2 login flow
    Redirects user to Discord authorization page
    """
    try:
        if not is_enabled():
            return JsonResponse({
                'status': 0,
                'error_message': 'Discord authentication is not enabled'
            })
        
        # Generate state and store in session
        state = generate_state()
        request.session['discord_oauth_state'] = state
        request.session['discord_oauth_redirect'] = request.GET.get('redirect', '/')
        
        # Get authorization URL
        auth_url, state = get_authorization_url(request, state)
        
        if not auth_url:
            return JsonResponse({
                'status': 0,
                'error_message': 'Failed to generate authorization URL'
            })
        
        # Redirect to Discord
        return redirect(auth_url)
        
    except Exception as e:
        logging.writeToFile(f"Discord login error: {str(e)}")
        return JsonResponse({
            'status': 0,
            'error_message': 'An error occurred during Discord login'
        })


@csrf_exempt
@require_http_methods(["GET"])
def discord_callback(request):
    """
    Handle Discord OAuth2 callback
    Exchanges code for token and logs user in
    """
    try:
        # Verify state
        stored_state = request.session.get('discord_oauth_state')
        received_state = request.GET.get('state')
        
        if not stored_state or stored_state != received_state:
            logging.writeToFile("Discord OAuth: Invalid state parameter")
            return redirect('/login?error=invalid_state')
        
        # Get authorization code
        code = request.GET.get('code')
        if not code:
            error = request.GET.get('error', 'unknown_error')
            logging.writeToFile(f"Discord OAuth: Error from Discord - {error}")
            return redirect(f'/login?error={error}')
        
        # Exchange code for token
        token_data = exchange_code_for_token(code, request)
        if not token_data:
            return redirect('/login?error=token_exchange_failed')
        
        # Get Discord user data
        discord_user = get_discord_user(token_data['access_token'])
        if not discord_user:
            return redirect('/login?error=user_fetch_failed')
        
        # Find or create CyberPanel admin account
        admin = None
        
        # Try to find existing Discord account link
        try:
            discord_account = DiscordAccount.objects.get(
                discord_id=discord_user['id'],
                is_active=True
            )
            admin = discord_account.admin
            # Update last used timestamp
            discord_account.save()
        except DiscordAccount.DoesNotExist:
            # Check if we should auto-create users
            config = get_config()
            if config.get('auto_create_users'):
                # Create new admin account
                admin = create_admin_from_discord(discord_user, config)
                if admin:
                    # Create Discord account link
                    create_discord_account_link(admin, discord_user)
            else:
                # User doesn't exist and auto-create is disabled
                return redirect('/login?error=account_not_found')
        
        if not admin:
            return redirect('/login?error=account_creation_failed')
        
        # Log user in
        request.session['userID'] = admin.pk
        
        # Set IP address
        ipAddr = request.META.get('HTTP_CF_CONNECTING_IP')
        if ipAddr is None:
            ipAddr = request.META.get('REMOTE_ADDR')
        if ipAddr.find(':') > -1:
            ipAddr = ':'.join(ipAddr.split(':')[:3])
        request.session['ipAddr'] = ipAddr
        
        # Set session expiry
        request.session.set_expiry(43200)
        
        # Clear OAuth state
        if 'discord_oauth_state' in request.session:
            del request.session['discord_oauth_state']
        
        # Redirect to original destination or dashboard
        redirect_url = request.session.get('discord_oauth_redirect', '/')
        if 'discord_oauth_redirect' in request.session:
            del request.session['discord_oauth_redirect']
        
        from baseTemplate.views import renderBase
        return redirect(renderBase)
        
    except Exception as e:
        logging.writeToFile(f"Discord callback error: {str(e)}")
        return redirect('/login?error=callback_failed')


def create_admin_from_discord(discord_user, config):
    """
    Create new CyberPanel admin account from Discord user data
    """
    try:
        from loginSystem.models import ACL
        from plogical import hashPassword
        
        # Generate username from Discord username
        username = discord_user['username'].lower().replace(' ', '_')
        base_username = username
        
        # Ensure username is unique
        counter = 1
        while Administrator.objects.filter(userName=username).exists():
            username = f"{base_username}_{counter}"
            counter += 1
        
        # Get default ACL
        default_acl_name = config.get('default_acl', 'user')
        try:
            acl = ACL.objects.get(name=default_acl_name)
        except ACL.DoesNotExist:
            acl = ACL.objects.first()
        
        # Generate random password (user won't need it with Discord auth)
        import secrets
        random_password = secrets.token_urlsafe(32)
        password_hash = hashPassword.hash_password(random_password)
        
        # Create admin
        admin = Administrator(
            userName=username,
            password=password_hash,
            email=discord_user.get('email', ''),
            firstName=discord_user['username'],
            lastName='',
            type=0,  # Regular user
            acl=acl
        )
        admin.save()
        
        logging.writeToFile(f"Created new admin account from Discord: {username}")
        return admin
        
    except Exception as e:
        logging.writeToFile(f"Error creating admin from Discord: {str(e)}")
        return None


def create_discord_account_link(admin, discord_user):
    """
    Create or update Discord account link
    """
    try:
        discord_account, created = DiscordAccount.objects.get_or_create(
            admin=admin,
            defaults={
                'discord_id': discord_user['id'],
                'discord_username': discord_user['username'],
                'discord_discriminator': discord_user.get('discriminator', '0'),
                'discord_email': discord_user.get('email', ''),
                'discord_avatar': discord_user.get('avatar_url', ''),
                'is_active': True
            }
        )
        
        if not created:
            # Update existing link
            discord_account.discord_username = discord_user['username']
            discord_account.discord_discriminator = discord_user.get('discriminator', '0')
            discord_account.discord_email = discord_user.get('email', '')
            discord_account.discord_avatar = discord_user.get('avatar_url', '')
            discord_account.is_active = True
            discord_account.save()
        
        return discord_account
        
    except Exception as e:
        logging.writeToFile(f"Error creating Discord account link: {str(e)}")
        return None


@cyberpanel_login_required
def main_view(request):
    """Main plugin view"""
    mailUtilities.checkHome()
    
    try:
        userID = request.session['userID']
        admin = Administrator.objects.get(pk=userID)
        
        # Check if user has Discord account linked
        discord_account = None
        try:
            discord_account = DiscordAccount.objects.get(admin=admin, is_active=True)
        except DiscordAccount.DoesNotExist:
            pass
        
        config = get_config()
        
        context = {
            'plugin_name': 'Discord Authentication',
            'version': '1.0.0',
            'enabled': config.get('enabled', False),
            'discord_account': discord_account,
            'has_discord': discord_account is not None
        }
        
        proc = httpProc(request, 'discordAuth/index.html', context, 'admin')
        return proc.render()
        
    except Exception as e:
        logging.writeToFile(f"Discord auth main view error: {str(e)}")
        return JsonResponse({'status': 0, 'error_message': str(e)})


@cyberpanel_login_required
def settings_view(request):
    """Settings page for Discord authentication"""
    mailUtilities.checkHome()
    
    try:
        userID = request.session['userID']
        currentACL = ACLManager.loadedACL(userID)
        
        if currentACL['admin'] != 1:
            return JsonResponse({
                'status': 0,
                'error_message': 'Admin access required'
            })
        
        config = get_config()
        
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                
                new_config = {
                    'client_id': data.get('client_id', ''),
                    'client_secret': data.get('client_secret', ''),
                    'redirect_uri': data.get('redirect_uri', ''),
                    'scope': data.get('scope', 'identify email'),
                    'enabled': data.get('enabled', False),
                    'auto_create_users': data.get('auto_create_users', False),
                    'default_acl': data.get('default_acl', 'user')
                }
                
                if save_config(new_config):
                    return JsonResponse({
                        'status': 1,
                        'error_message': 'Settings saved successfully'
                    })
                else:
                    return JsonResponse({
                        'status': 0,
                        'error_message': 'Failed to save settings'
                    })
                    
            except Exception as e:
                logging.writeToFile(f"Error saving Discord settings: {str(e)}")
                return JsonResponse({
                    'status': 0,
                    'error_message': str(e)
                })
        
        # Get redirect URI suggestion
        scheme = 'https' if request.is_secure() else 'http'
        host = request.get_host()
        suggested_redirect = f"{scheme}://{host}/plugins/discordAuth/callback/"
        
        context = {
            'plugin_name': 'Discord Authentication',
            'version': '1.0.0',
            'config': config,
            'suggested_redirect_uri': suggested_redirect
        }
        
        proc = httpProc(request, 'discordAuth/settings.html', context, 'admin')
        return proc.render()
        
    except Exception as e:
        logging.writeToFile(f"Discord auth settings error: {str(e)}")
        return JsonResponse({'status': 0, 'error_message': str(e)})
