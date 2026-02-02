# -*- coding: utf-8 -*-
from django.urls import path
from . import views

app_name = 'redisManager'

urlpatterns = [
    path('', views.main_view, name='main'),
    path('api/control/', views.api_control, name='api_control'),
    path('api/flush/', views.api_flush, name='api_flush'),
    path('api/config/', views.api_config, name='api_config'),
    path('api/save-config/', views.api_save_config, name='api_save_config'),
    path('api/detect-config/', views.api_detect_config, name='api_detect_config'),
    path('api/save-config-path/', views.api_save_config_path, name='api_save_config_path'),
    path('api/fix-permissions/', views.api_fix_permissions, name='api_fix_permissions'),
]
