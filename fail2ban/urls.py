from django.urls import re_path
from . import views

urlpatterns = [
    # Main plugin page (required by CyberPanel)
    re_path(r'^$', views.fail2ban_plugin, name='fail2ban_plugin'),
    
    # Standalone pages
    re_path(r'^dashboard/$', views.dashboard, name='dashboard_alt'),
    re_path(r'^jails/$', views.jails_standalone, name='jails_standalone'),
    re_path(r'^banned-ips/$', views.banned_ips_standalone, name='banned_ips_standalone'),
    re_path(r'^whitelist/$', views.whitelist_standalone, name='whitelist_standalone'),
    re_path(r'^blacklist/$', views.blacklist_standalone, name='blacklist_standalone'),
    re_path(r'^logs/$', views.logs_standalone, name='logs_standalone'),
    re_path(r'^statistics/$', views.statistics_standalone, name='statistics_standalone'),
    re_path(r'^settings/$', views.settings_standalone, name='settings_standalone'),
    
    # Plugin card
    re_path(r'^card/$', views.plugin_card, name='plugin_card'),
    
    # API endpoints
    re_path(r'^api/status/$', views.api_status, name='api_status'),
    re_path(r'^api/jails/$', views.api_jails, name='api_jails'),
    re_path(r'^api/banned-ips/$', views.api_banned_ips, name='api_banned_ips'),
    re_path(r'^api/whitelist/$', views.api_whitelist, name='api_whitelist'),
    re_path(r'^api/blacklist/$', views.api_blacklist, name='api_blacklist'),
    re_path(r'^api/ban-ip/$', views.api_ban_ip, name='api_ban_ip'),
    re_path(r'^api/unban-ip/$', views.api_unban_ip, name='api_unban_ip'),
    re_path(r'^api/restart/$', views.api_restart, name='api_restart'),
    re_path(r'^api/restart-litespeed/$', views.api_restart_litespeed, name='api_restart_litespeed'),
    re_path(r'^api/logs/$', views.api_logs, name='api_logs'),
    re_path(r'^api/settings/$', views.api_settings, name='api_settings'),
    re_path(r'^api/statistics/$', views.api_statistics, name='api_statistics'),
    re_path(r'^api/toggle-plugin/$', views.api_toggle_plugin, name='api_toggle_plugin'),
    
    # Legacy unified settings (for backward compatibility)
    re_path(r'^unified/$', views.unified_settings, name='unified_settings'),
]
