# -*- coding: utf-8 -*-
from django.urls import path
from . import views

app_name = 'snappymailWebmail'

urlpatterns = [
    path('', views.admin_settings, name='main'),
    path('settings/', views.admin_settings, name='settings'),
    path('api/toggle/', views.api_toggle, name='api_toggle'),
    path('api/status/', views.api_status, name='api_status'),
]
