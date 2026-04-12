# -*- coding: utf-8 -*-
"""HTML page views for Fail2ban plugin."""
from django.shortcuts import render
from django.http import HttpResponse

from .utils import Fail2banManager
from .panel_auth import cyberpanel_login_and_admin, _html_plugin_error


@cyberpanel_login_and_admin
def fail2ban_plugin(request):
    """Main plugin page (required by CyberPanel)"""
    try:
        manager = Fail2banManager()
        status = manager.get_status()

        context = {
            'title': 'Fail2ban Security Manager',
            'status': status,
        }
        return render(request, 'fail2ban_plugin/dashboard.html', context)
    except Exception as e:
        return _html_plugin_error(request, e, 'Plugin')


@cyberpanel_login_and_admin
def plugin_card(request):
    """Plugin card view with buttons"""
    try:
        context = {
            'title': 'Settings Plugin Card'
        }
        return render(request, 'fail2ban_plugin/plugin_card.html', context)
    except Exception as e:
        return _html_plugin_error(request, e, 'Plugin card')


@cyberpanel_login_and_admin
def jails_standalone(request):
    """Standalone jails management page"""
    try:
        manager = Fail2banManager()
        jails = manager.get_jails()

        context = {
            'title': 'Jail Management',
            'jails': jails,
        }
        return render(request, 'fail2ban_plugin/jails_standalone.html', context)
    except Exception as e:
        return _html_plugin_error(request, e, 'Jails')


@cyberpanel_login_and_admin
def banned_ips_standalone(request):
    """Standalone banned IPs page"""
    try:
        manager = Fail2banManager()
        banned_ips = manager.get_banned_ips()

        context = {
            'title': 'Banned IPs',
            'banned_ips': banned_ips,
        }
        return render(request, 'fail2ban_plugin/banned_ips_standalone.html', context)
    except Exception as e:
        return _html_plugin_error(request, e, 'Banned IPs')


@cyberpanel_login_and_admin
def whitelist_standalone(request):
    """Standalone whitelist page"""
    try:
        manager = Fail2banManager()
        whitelist = manager.get_whitelist()

        context = {
            'title': 'IP Whitelist Management',
            'whitelist': whitelist,
        }
        return render(request, 'fail2ban_plugin/whitelist_standalone.html', context)
    except Exception as e:
        return _html_plugin_error(request, e, 'Whitelist')


@cyberpanel_login_and_admin
def blacklist_standalone(request):
    """Standalone blacklist page"""
    try:
        manager = Fail2banManager()
        blacklist = manager.get_blacklist()

        context = {
            'title': 'IP Blacklist Management',
            'blacklist': blacklist,
        }
        return render(request, 'fail2ban_plugin/blacklist_standalone.html', context)
    except Exception as e:
        return _html_plugin_error(request, e, 'Blacklist')


@cyberpanel_login_and_admin
def logs_standalone(request):
    """Standalone logs page"""
    try:
        context = {
            'title': 'Security Logs',
        }
        return render(request, 'fail2ban_plugin/logs_standalone.html', context)
    except Exception as e:
        return _html_plugin_error(request, e, 'Logs')


@cyberpanel_login_and_admin
def statistics_standalone(request):
    """Standalone statistics page"""
    try:
        context = {
            'title': 'Security Statistics',
        }
        return render(request, 'fail2ban_plugin/statistics_standalone.html', context)
    except Exception as e:
        return _html_plugin_error(request, e, 'Statistics')


@cyberpanel_login_and_admin
def settings_standalone(request):
    """Standalone settings page"""
    try:
        context = {
            'title': 'Settings',
        }
        return render(request, 'fail2ban_plugin/settings_standalone.html', context)
    except Exception as e:
        return _html_plugin_error(request, e, 'Settings')


@cyberpanel_login_and_admin
def unified_settings(request):
    """Unified settings view with tabs"""
    try:
        active_tab = request.GET.get('tab', 'overview')

        if active_tab == 'overview':
            path = request.path_info
            if 'jails' in path:
                active_tab = 'jails'
            elif 'banned-ips' in path:
                active_tab = 'banned-ips'
            elif 'whitelist' in path:
                active_tab = 'whitelist'
            elif 'blacklist' in path:
                active_tab = 'blacklist'
            elif 'logs' in path:
                active_tab = 'logs'
            elif 'statistics' in path:
                active_tab = 'statistics'
            elif 'settings' in path:
                active_tab = 'settings'

        manager = Fail2banManager()
        status = manager.get_status()

        context = {
            'title': 'Settings',
            'active_tab': active_tab,
            'status': status,
            'tabs': [
                {'id': 'overview', 'name': 'Overview', 'icon': '📊'},
                {'id': 'jails', 'name': 'Manage Jails', 'icon': '🔒'},
                {'id': 'banned-ips', 'name': 'Banned IPs', 'icon': '🚫'},
                {'id': 'whitelist', 'name': 'Whitelist', 'icon': '✅'},
                {'id': 'blacklist', 'name': 'Blacklist', 'icon': '⚫'},
                {'id': 'logs', 'name': 'Security Logs', 'icon': '📋'},
                {'id': 'statistics', 'name': 'Statistics', 'icon': '📈'},
                {'id': 'settings', 'name': 'Settings', 'icon': '⚙️'},
            ]
        }
        return render(request, 'fail2ban_plugin/clean_settings.html', context)
    except Exception as e:
        return _html_plugin_error(request, e, 'Unified settings')


@cyberpanel_login_and_admin
def dashboard(request):
    """Legacy dashboard view - redirects to unified settings"""
    return unified_settings(request)


@cyberpanel_login_and_admin
def jails_management(request):
    """Jails management page"""
    context = {
        'title': 'Jails Management',
        'active_tab': 'jails'
    }
    return render(request, 'fail2ban_plugin/jails.html', context)


@cyberpanel_login_and_admin
def banned_ips_management(request):
    """Banned IPs management page"""
    context = {
        'title': 'Banned IPs Management',
        'active_tab': 'banned_ips'
    }
    return render(request, 'fail2ban_plugin/banned_ips.html', context)


@cyberpanel_login_and_admin
def whitelist_management(request):
    """Whitelist management page"""
    context = {
        'title': 'Whitelist Management',
        'active_tab': 'whitelist'
    }
    return render(request, 'fail2ban_plugin/whitelist.html', context)


@cyberpanel_login_and_admin
def blacklist_management(request):
    """Blacklist management page"""
    context = {
        'title': 'Blacklist Management',
        'active_tab': 'blacklist'
    }
    return render(request, 'fail2ban_plugin/blacklist.html', context)


@cyberpanel_login_and_admin
def settings_management(request):
    """Settings management page"""
    context = {
        'title': 'Settings Management',
        'active_tab': 'settings'
    }
    return render(request, 'fail2ban_plugin/settings.html', context)


@cyberpanel_login_and_admin
def logs_view(request):
    """Logs view page"""
    context = {
        'title': 'Security Logs',
        'active_tab': 'logs'
    }
    return render(request, 'fail2ban_plugin/logs.html', context)


@cyberpanel_login_and_admin
def statistics_view(request):
    """Statistics view page"""
    context = {
        'title': 'Security Statistics',
        'active_tab': 'statistics'
    }
    return render(request, 'fail2ban_plugin/statistics.html', context)
