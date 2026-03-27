# -*- coding: utf-8 -*-
from django.urls import path
from . import pma_launch
from . import views

app_name = 'limitedPhpmyAdmin'

urlpatterns = [
    path('', views.main_view, name='limitedPhpmyAdmin'),
    path('settings/', views.main_view, name='settings'),
    path('api/domains/', views.api_list_domains, name='api_domains'),
    path('api/databases/', views.api_list_databases, name='api_databases'),
    path('api/ftp/', views.api_list_ftp, name='api_ftp'),
    path('api/cpusers/', views.api_list_cpusers, name='api_cpusers'),
    path('api/grants/', views.api_list_grants, name='api_grants'),
    path('api/grants/create/', views.api_create_grant, name='api_create_grant'),
    path('api/grants/disable/', views.api_disable_grant, name='api_disable_grant'),
    path('api/grants/enable/', views.api_enable_grant, name='api_enable_grant'),
    path('api/grants/delete/', views.api_delete_grant, name='api_delete_grant'),
    path('api/grants/rotate-password/', views.api_rotate_password, name='api_rotate_password'),
    path('api/grants/change-database/', views.api_change_database, name='api_change_database'),
    path('api/grants/update-privileges/', views.api_update_privileges, name='api_update_privileges'),
    path('api/grants/notes/', views.api_update_notes, name='api_update_notes'),
    path('api/policy/', views.api_get_policy, name='api_get_policy'),
    path('api/policy/update/', views.api_update_policy, name='api_update_policy'),
    path('api/grants/pma-launch-link/', pma_launch.api_create_pma_launch_link, name='api_pma_launch_link'),
    path('launch/<str:token>/', pma_launch.pma_launch, name='pma_launch'),
]
