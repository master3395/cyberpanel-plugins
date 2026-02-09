# -*- coding: utf-8 -*-
from django.urls import path
from . import views

app_name = 'panelAccess'

urlpatterns = [
    path('', views.settings_page, name='panel_access_settings'),
    path('save', views.save_origins, name='panel_access_save'),
]
