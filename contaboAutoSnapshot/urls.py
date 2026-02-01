from django.urls import re_path
from . import views

app_name = 'contaboAutoSnapshot'

urlpatterns = [
    # Main plugin page (required by CyberPanel)
    re_path(r'^$', views.main_view, name='main'),
    
    # Settings page
    re_path(r'^settings/$', views.settings_view, name='settings'),
    # Test view (temporary - no decorators)
    re_path(r'^test/$', views.test_view_no_decorator, name='test'),
    
    # Snapshot schedule management
    re_path(r'^schedule/add/$', views.add_schedule, name='add_schedule'),
    re_path(r'^schedule/(?P<schedule_id>\d+)/edit/$', views.edit_schedule, name='edit_schedule'),
    re_path(r'^schedule/(?P<schedule_id>\d+)/delete/$', views.delete_schedule, name='delete_schedule'),
    re_path(r'^schedule/(?P<schedule_id>\d+)/toggle/$', views.toggle_schedule, name='toggle_schedule'),
    
    # Manual snapshot creation
    re_path(r'^snapshot/create/$', views.create_snapshot, name='create_snapshot'),
    
    # Snapshot history and management
    re_path(r'^snapshots/$', views.snapshot_history, name='snapshot_history'),
    re_path(r'^snapshot/(?P<snapshot_id>\d+)/delete/$', views.delete_snapshot, name='delete_snapshot'),
    
    # API endpoints
    re_path(r'^api/schedules/$', views.api_schedules, name='api_schedules'),
    re_path(r'^api/snapshots/$', views.api_snapshots, name='api_snapshots'),
    re_path(r'^api/test-connection/$', views.test_connection, name='test_connection'),
    re_path(r'^config/save/$', views.save_config, name='save_config'),
    re_path(r'^activate-key/$', views.activate_key, name='activate_key'),
]
