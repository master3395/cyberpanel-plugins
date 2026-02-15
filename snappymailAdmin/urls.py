# -*- coding: utf-8 -*-
from django.urls import path
from . import views

app_name = 'snappymailAdmin'

urlpatterns = [
    path('', views.main_view, name='main'),
    path('settings/', views.main_view, name='settings'),
    path('api/set-password/', views.api_set_password, name='api_set_password'),
]
