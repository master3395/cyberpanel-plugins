# -*- coding: utf-8 -*-
from django.urls import path
from . import views

app_name = 'postgresManager'

urlpatterns = [
    path('', views.main_view, name='main'),
    path('settings/', views.main_view, name='settings'),
    path('api/control/', views.api_control, name='api_control'),
    path('api/init-admin/', views.api_init_admin, name='api_init_admin'),
]
