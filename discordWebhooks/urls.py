from django.urls import re_path
from . import views

app_name = 'discordWebhooks'

urlpatterns = [
    # Main plugin page (required by CyberPanel)
    re_path(r'^$', views.discord_webhooks_plugin, name='discord_webhooks_plugin'),
    
    # Settings page
    re_path(r'^settings/$', views.settings_view, name='settings'),
    
    # Webhook management
    re_path(r'^webhook/add/$', views.add_webhook, name='add_webhook'),
    re_path(r'^webhook/(?P<webhook_id>\d+)/edit/$', views.edit_webhook, name='edit_webhook'),
    re_path(r'^webhook/(?P<webhook_id>\d+)/delete/$', views.delete_webhook, name='delete_webhook'),
    re_path(r'^webhook/(?P<webhook_id>\d+)/test/$', views.test_webhook, name='test_webhook'),
    
    # Settings management
    re_path(r'^settings/save/$', views.save_settings, name='save_settings'),
]
