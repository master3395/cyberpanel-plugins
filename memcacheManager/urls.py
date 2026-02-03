# -*- coding: utf-8 -*-
from django.urls import path
from . import views

app_name = 'memcacheManager'

urlpatterns = [
    path('', views.main_view, name='main'),
    path('settings/', views.main_view, name='settings'),
    path('api/control/', views.api_control, name='api_control'),
    path('api/stats/', views.api_stats, name='api_stats'),
    path('api/flush/', views.api_flush, name='api_flush'),
    path('api/config/', views.api_config, name='api_config'),
]
