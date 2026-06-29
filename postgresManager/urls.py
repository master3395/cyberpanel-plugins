# -*- coding: utf-8 -*-
from django.urls import path
from . import views

app_name = 'postgresManager'

urlpatterns = [
    path('', views.main_view, name='main'),
    path('settings/', views.main_view, name='settings'),
    path('api/control/', views.api_control, name='api_control'),
    path('api/init-admin/', views.api_init_admin, name='api_init_admin'),
    path('api/websites/', views.api_websites, name='api_websites'),
    path('api/databases/', views.api_databases, name='api_databases'),
    path('api/create-database/', views.api_create_database, name='api_create_database'),
    path('api/change-password/', views.api_change_password, name='api_change_password'),
    path('api/delete-database/', views.api_delete_database, name='api_delete_database'),
]
