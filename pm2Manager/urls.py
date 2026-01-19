# -*- coding: utf-8 -*-
from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('settings/', views.settings, name='settings'),
    path('node/<str:app_name>/', views.node_detail, name='node_detail'),
    
    # API endpoints
    path('api/list/', views.api_list_apps, name='api_list'),
    path('api/start/<str:app_name>/', views.api_start_app, name='api_start'),
    path('api/stop/<str:app_name>/', views.api_stop_app, name='api_stop'),
    path('api/restart/<str:app_name>/', views.api_restart_app, name='api_restart'),
    path('api/delete/<str:app_name>/', views.api_delete_app, name='api_delete'),
    path('api/add/', views.api_add_app, name='api_add'),
    path('api/info/<str:app_name>/', views.api_get_info, name='api_info'),
    path('api/logs/<str:app_name>/', views.api_get_logs, name='api_logs'),
    path('api/monitor/', views.api_monitor, name='api_monitor'),
]
