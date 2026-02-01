# -*- coding: utf-8 -*-
from django.urls import path
from . import views

app_name = 'cspManager'

urlpatterns = [
    path('', views.main_view, name='main'),
    path('settings/', views.settings_view, name='settings'),
    path('api/toggle-plugin/', views.toggle_plugin_csp, name='toggle_plugin'),
]
